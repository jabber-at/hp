# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If
# not, see <http://www.gnu.org/licenses/>.

from datetime import datetime

import pytz
from freezegun import freeze_time

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.tests import TestCase

from .tasks import send_confirmation_task

User = get_user_model()


class RegistrationTestCase(TestCase):
    def test_basic(self):
        now = pytz.utc.localize(datetime(2017, 4, 23, 11, 22, 33))
        url = reverse('account:register')
        client = Client()

        self.assertEqual(User.objects.count(), 0)

        get = client.get(url)
        self.assertEqual(get.status_code, 200)
        self.assertTrue(get.context['user'].is_anonymous)
        self.assertTrue('form' in get.context)

        with self.mock_celery() as func, freeze_time('2017-04-23 11:22:33+00:00'):
            post = client.post(url, {
                'username_0': 'testuser', 'username_1': 'example.com', 'email': 'user@example.com',
            }, follow=True)

        self.assertTaskCall(func, send_confirmation_task, **{
            'address': '127.0.0.1',
            'base_url': 'http://testserver',
            'hostname': 'example.com',
            'language': 'en',
            'purpose': 'register',
            'to': 'user@example.com',
            'user_pk': 1,
        })

        self.assertFalse(post.context['user'].is_anonymous)
        self.assertRedirects(post, reverse('account:detail'))

        # redirects don't have a context, so we login now
        client.force_login(User.objects.get(username='testuser@example.com'))
        detail = client.get(reverse('account:detail'))
        self.assertFalse(detail.context['user'].is_anonymous)

        # Examine user
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user, detail.context['user'])
        self.assertEqual(user.username, 'testuser@example.com')
        self.assertEqual(user.email, 'user@example.com')
        self.assertEqual(user.registered, now)
        self.assertIsNone(user.confirmed)
        self.assertFalse(user.blocked)
        self.assertEqual(user.last_activity, now)
        self.assertFalse(user.created_in_backend)
        self.assertEqual(user.default_language, 'en')

        # TODO
        # Check confirmation
        # Check email inbox
        # Check XMPP backend (user should not be present)
        # Confirm email address
        # Check updated user
        # Check XMPP backend (user should be present)
