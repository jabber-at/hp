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

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.test import Client
from django.test import override_settings
from django.urls import reverse

from ..forms import AnonymousContactForm
from ..tasks import send_contact_email
from .base import HomepageTestCaseMixin
from .base import TestCase

SUBJECT = 'a' * 15
TEXT = 'b' * 110
EMAIL = 'user@example.com'


class ContactTestCaseMixin(object):
    def assertEmail(self, site, addr, mocked, email=EMAIL, subject=SUBJECT, text=TEXT):
        # Test that the contact call was correctly called
        self.assertTaskCount(mocked, 1)
        self.assertTaskCall(
            mocked, send_contact_email,
            site['NAME'], SUBJECT, TEXT,
            user_pk=None, recipient=EMAIL, address=addr
        )

        from_email = site.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        to_email = site['CONTACT_ADDRESS']
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
            'X-Homepage-Submit-Address': addr,
        })
        self.assertEqual(mail.outbox[0].attachments, [])


class AnonymousContactViewTests(ContactTestCaseMixin, TestCase):
    def _post_form(self, data=None):
        if data is None:
            data = {}

        data.setdefault('subject', SUBJECT)
        data.setdefault('text', TEXT)
        data.setdefault('email', EMAIL)

        url = reverse('core:contact')
        c = Client()

        with self.mock_celery() as mocked, self.assertTemplateUsed('core/contact.html'):
            return c.post(url, data), mocked

    def assertEmail(self, response, mocked, **kwargs):
        site = response.wsgi_request.site
        address = response.wsgi_request.META['REMOTE_ADDR']
        super().assertEmail(site, address, mocked, **kwargs)

        # Test response
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AnonymousContactForm)

        # Test form
        form = response.context['form']
        self.assertIsInstance(form, AnonymousContactForm)
        self.assertTrue(form.is_bound)
        self.assertEqual(form.errors, {})

    def assertFormError(self, response, mocked, *errors):
        form = response.context['form']

        # Some basic assertions
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(form, AnonymousContactForm)

        # Test that no email was sent
        self.assertTaskCount(mocked, 0)
        self.assertEqual(len(mail.outbox), 0)

        # Check passed errors
        self.assertTrue(form.is_bound)
        for error in errors:
            self.assertIn(error, form.errors)

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
        # simulates a successful form submit
        response, mocked = self._post_form()
        self.assertEmail(response, mocked)
        # TODO: Test html fragments on form submit

    def test_post_invalid_form(self):
        response, mocked = self._post_form(data={'email': '', 'subject': '', 'text': ''})
        self.assertFormError(response, mocked, 'subject', 'text', 'email')

    #################
    # CAPTCHA tests #
    #################
    @override_settings(ENABLE_CAPTCHAS=True)
    def test_post_captcha(self):
        response, mocked = self._post_form(data={'captcha_0': 'dummy-value', 'captcha_1': 'PASSED'})
        self.assertEmail(response, mocked)

    @override_settings(ENABLE_CAPTCHAS=True)
    def test_post_captcha_missing(self):
        response, mocked = self._post_form()
        self.assertFormError(response, mocked, 'captcha')

    @override_settings(ENABLE_CAPTCHAS=True)
    def test_post_wrong_captcha(self):
        response, mocked = self._post_form(data={'captcha_0': 'dummy-value', 'captcha_1': 'WRONG'})
        self.assertFormError(response, mocked, 'captcha')


class ContactSeleniumTests(HomepageTestCaseMixin, ContactTestCaseMixin, StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver(executable_path=settings.GECKODRIVER_PATH)
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_basic(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('core:contact')))
        self.selenium.find_element_by_id('id_email').send_keys(EMAIL)
        self.selenium.find_element_by_id('id_subject').send_keys(SUBJECT)
        self.selenium.find_element_by_id('id_text').send_keys(TEXT)

        with self.mock_celery() as mocked:
            self.selenium.find_element_by_css_selector('button[type="submit"]').click()

        WebDriverWait(self.selenium, 2).until(
            lambda driver: driver.find_element_by_tag_name('body'))

        site = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]
        self.assertEmail(site, '127.0.0.1', mocked, email=EMAIL, subject=SUBJECT, text=TEXT)
