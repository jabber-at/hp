# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

from contextlib import contextmanager
from unittest.mock import patch

from django.core import mail
from django.conf import settings
#from django.conf.urls import include
#from django.conf.urls import url
from django.test import Client
#from django.test import override_settings
from django.urls import reverse
#from django.utils.translation import ugettext_lazy as _

from ..forms import AnonymousContactForm
from ..tasks import send_contact_email
#from .. import viewas
#from ..urlpatterns import i18n_re_path
from .base import TestCase


class AnonymousContactViewTests(TestCase):
    @contextmanager
    def mock_tasks(self):
        with patch('celery.app.task.Task.apply_async') as mock:
            yield mock

    @contextmanager
    def mock_task(self, task):
        task_path = '%s.%s.delay' % (task.__module__, task.__name__)

        with patch(task_path, side_effect=task) as mock:
            yield mock
            self.assertTrue(mock.called)

    def test_get(self):
        url = reverse('core:contact')
        c = Client()
        with self.assertTemplateUsed('core/contact.html'):
            response = c.get(url)
        self.assertEqual(response.status_code, 200)

        # test form
        form = response.context['form']
        self.assertIsInstance(form, AnonymousContactForm)
        self.assertFalse(form.is_bound)

    def test_post(self):
        url = reverse('core:contact')
        c = Client()
        subject = 'a' * 15
        text = 'b' * 200
        email = 'user@example.com'

        with self.mock_celery() as mocked, self.assertTemplateUsed('core/contact.html'):
            response = c.post(url, {'subject': subject, 'text': text, 'email': email})

        # Test that the contact call was correctly called
        self.assertTaskCount(mocked, 1)
        self.assertTaskCall(
            mocked, send_contact_email,
            response.wsgi_request.site['NAME'], subject, text,
            user_pk=None, recipient=email, address=response.wsgi_request.META['REMOTE_ADDR']
        )

        # Test response
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AnonymousContactForm)

        # Test form
        form = response.context['form']
        self.assertIsInstance(form, AnonymousContactForm)
        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {})

        # Test email that was sent
        from_email = response.wsgi_request.site.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        to_email = response.wsgi_request.site['CONTACT_ADDRESS']
        replyto_email = [to_email, email]
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].from_email, from_email)
        self.assertEqual(mail.outbox[0].to, [to_email])
        self.assertEqual(mail.outbox[0].cc, [])
        self.assertEqual(mail.outbox[0].bcc, [])
        self.assertCountEqual(mail.outbox[0].reply_to, replyto_email)
        self.assertEqual(mail.outbox[0].body, text)
        self.assertEqual(mail.outbox[0].extra_headers, {
            'X-Homepage-Submit-Address': response.wsgi_request.META['REMOTE_ADDR'],
        })
        self.assertEqual(mail.outbox[0].attachments, [])

    def test_post_invalid_form(self):
        url = reverse('core:contact')
        c = Client()

        with self.mock_celery() as mocked, self.assertTemplateUsed('core/contact.html'):
            response = c.post(url, {'subject': 'subject 1', 'text': 'text 1', 'email': 'user'})
            self.assertTaskCount(mocked, 0)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AnonymousContactForm)

        form = response.context['form']
        self.assertIsInstance(form, AnonymousContactForm)
        self.assertTrue(form.is_bound)
        self.assertIn('subject', form.errors)
        self.assertIn('text', form.errors)
        self.assertIn('email', form.errors)
