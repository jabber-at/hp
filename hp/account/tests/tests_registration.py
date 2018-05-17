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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils.translation import get_language

from xmpp_backends.django import xmpp_backend

from core.models import Address
from core.tests.base import SeleniumTestCase
from core.tests.base import TestCase

from ..constants import PURPOSE_REGISTER
from ..models import Confirmation
from ..tasks import send_confirmation_task

User = get_user_model()
NOW = pytz.utc.localize(datetime(2017, 4, 23, 11, 22, 33))
NOW_STR = '2017-04-23 11:22:33+00:00'
NOW2 = pytz.utc.localize(datetime(2017, 4, 23, 12, 23, 34))
NOW2_STR = '2017-04-23 12:23:34+00:00'

NODE = 'user'
DOMAIN = 'example.com'
JID = '%s@%s' % (NODE, DOMAIN)
EMAIL = 'user@example.com'
PWD = 'password123'
PWD2 = 'password456'


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

        with self.mock_celery() as func, freeze_time(NOW_STR):
            post = client.post(url, {
                'username_0': NODE, 'username_1': DOMAIN, 'email': EMAIL,
            }, follow=True)

        self.assertTaskCall(func, send_confirmation_task, **{
            'address': '127.0.0.1',
            'base_url': 'http://testserver',
            'hostname': 'example.com',
            'language': 'en',
            'purpose': 'register',
            'to': EMAIL,
            'user_pk': 1,
        })

        self.assertFalse(post.context['user'].is_anonymous)
        self.assertRedirects(post, reverse('account:detail'))

        # redirects don't have a context, so we login now
        client.force_login(User.objects.get(username=JID))
        detail = client.get(reverse('account:detail'))
        self.assertFalse(detail.context['user'].is_anonymous)

        # Examine user
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user, detail.context['user'])
        self.assertEqual(user.username, JID)
        self.assertEqual(user.email, EMAIL)
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


class RegisterSeleniumTests(SeleniumTestCase):
    def test_registration(self):
        """Test basic registration."""
        self.selenium.get('%s%s' % (self.live_server_url, reverse('account:register')))

        #fg_username = self.find('#fg_username')
        node = self.selenium.find_element_by_id('id_username_0')
        #domain = self.selenium.find_element_by_id('id_username_1')
        #fg_email = self.find('#fg_email')
        email = self.selenium.find_element_by_id('id_email')

        node.send_keys(NODE)
        email.send_keys(EMAIL)
        self.wait_for_valid_form()

        with self.mock_celery() as mocked, freeze_time(NOW_STR):
            self.selenium.find_element_by_css_selector('button[type="submit"]').click()
            self.wait_for_page_load()

        self.assertTaskCount(mocked, 1)

        user = User.objects.get(username='%s@%s' % (NODE, DOMAIN))
        lang = get_language().split('-', 1)[0]

        site = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]
        self.assertTaskCall(
            mocked, send_confirmation_task,
            user_pk=user.pk, purpose=PURPOSE_REGISTER, to=EMAIL, hostname=site['NAME'],
            base_url=self.live_server_url, language=lang, address='127.0.0.1'
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(user.registered, NOW)
        self.assertEqual(user.last_activity, NOW)
        self.assertIsNone(user.confirmed)
        self.assertFalse(user.created_in_backend)
        self.assertFalse(user.blocked)
        self.assertDisplayed('#email-confirmed.table-danger')

        confirmation = Confirmation.objects.get(user=user, purpose=PURPOSE_REGISTER)
        self.selenium.get('%s%s' % (self.live_server_url, confirmation.urlpath))
        self.wait_for_page_load()

        self.find('#id_new_password1').send_keys(PWD)
        self.find('#id_new_password2').send_keys(PWD)
        self.wait_for_valid_form()
        with freeze_time(NOW2_STR):
            self.find('button[type="submit"]').click()
            self.wait_for_page_load()

        # get user again
        user = User.objects.get(username='%s@%s' % (NODE, DOMAIN))
        self.assertEqual(user.confirmed, NOW2)
        # TODO: currently not updated?
        #self.assertEqual(user.last_activity, NOW2)
        self.assertTrue(user.check_password(PWD))
        self.assertTrue(xmpp_backend.check_password(user.node, user.domain, PWD))  # just to be sure
        self.assertTrue(user.created_in_backend)
        self.assertFalse(user.blocked)
        self.assertDisplayed('#email-confirmed.table-success')

    def test_password_validation(self):
        user = User.objects.create(username=JID, email=EMAIL)
        addr = Address.objects.create(address='127.0.0.1')
        conf = Confirmation.objects.create(user=user, purpose=PURPOSE_REGISTER, language='en',
                                           address=addr, to=EMAIL)

        self.selenium.get('%s%s' % (self.live_server_url, conf.urlpath))
        self.wait_for_page_load()

        fg_pwd = self.find('#fg_new_password1')
        pwd = fg_pwd.find_element_by_css_selector('#id_new_password1')
        fg_pwd2 = self.find('#fg_new_password2')
        pwd2 = fg_pwd2.find_element_by_css_selector('#id_new_password2')
        self.assertNotValidated(fg_pwd, pwd)
        self.assertNotValidated(fg_pwd2, pwd2)

        pwd.send_keys(PWD)
        pwd2.send_keys(PWD2)
        self.wait_for_valid(pwd)
        self.wait_for_invalid(pwd2)
        self.assertValid(fg_pwd, pwd)
        self.assertInvalid(fg_pwd2, pwd2, 'password_mismatch')

        # clear input - it's required though
        for i in range(0, len(PWD2)):
            pwd2.send_keys(Keys.BACKSPACE)
        self.assertValid(fg_pwd, pwd)
        self.assertInvalid(fg_pwd2, pwd2, 'required')

        # test server-side validation
        for i in range(0, len(PWD)):
            pwd.send_keys(Keys.BACKSPACE)
        pwd.send_keys('12345678')
        pwd2.send_keys('12345678')
        self.wait_for_valid(pwd)
        self.wait_for_valid(pwd2)
        self.assertValid(fg_pwd, pwd)
        self.assertValid(fg_pwd2, pwd2)

        self.find('button[type="submit"]').click()
        self.wait_for_page_load()

        fg_pwd = self.find('#fg_new_password1')
        pwd = fg_pwd.find_element_by_css_selector('#id_new_password1')
        fg_pwd2 = self.find('#fg_new_password2')
        pwd2 = fg_pwd2.find_element_by_css_selector('#id_new_password2')
        self.assertInvalid(fg_pwd, pwd, 'password_entirely_numeric', 'password_too_common')
        self.assertInvalid(fg_pwd2, pwd2, 'password_entirely_numeric', 'password_too_common')

        # Send JID as password, which is always "too similar"
        pwd.send_keys(JID)
        pwd2.send_keys(JID)
        self.find('button[type="submit"]').click()
        self.wait_for_page_load()

        fg_pwd = self.find('#fg_new_password1')
        pwd = fg_pwd.find_element_by_css_selector('#id_new_password1')
        fg_pwd2 = self.find('#fg_new_password2')
        pwd2 = fg_pwd2.find_element_by_css_selector('#id_new_password2')
        self.assertInvalid(fg_pwd, pwd, 'password_too_similar')
        self.assertInvalid(fg_pwd2, pwd2, 'password_too_similar')

        # send correct password
        pwd.send_keys(PWD)
        pwd2.send_keys(PWD)
        self.wait_for_valid(pwd2)
        self.assertValid(fg_pwd, pwd)
        self.assertValid(fg_pwd2, pwd2)

        self.wait_for_valid_form()
        with freeze_time(NOW2_STR):
            self.find('button[type="submit"]').click()
            self.wait_for_page_load()

        # get user again
        user = User.objects.get(username='%s@%s' % (NODE, DOMAIN))
        self.assertEqual(user.confirmed, NOW2)
        # TODO: currently not updated?
        #self.assertEqual(user.last_activity, NOW2)
        self.assertTrue(user.created_in_backend)
        self.assertTrue(user.check_password(PWD))
        self.assertTrue(xmpp_backend.check_password(user.node, user.domain, PWD))  # just to be sure
        self.assertFalse(user.blocked)

    def test_form_validation(self):
        # create a test user so we can test for colisions.
        User.objects.create(username='exists@example.com')

        self.selenium.get('%s%s' % (self.live_server_url, reverse('account:register')))

        fg_username = self.find('#fg_username')
        node = self.selenium.find_element_by_id('id_username_0')
        domain = self.selenium.find_element_by_id('id_username_1')
        fg_email = self.find('#fg_email')
        email = self.selenium.find_element_by_id('id_email')

        # test initial state
        self.assertNotValidated(fg_username, node)
        self.assertNotValidated(fg_username, domain)
        self.assertNotValidated(fg_email, email)

        # type one character, invalid because of min length
        node.send_keys('a')
        self.wait_for_invalid(node)
        self.assertInvalid(fg_username, node, 'min_length')
        self.assertInvalid(fg_username, domain, 'min_length')
        self.assertNotValidated(fg_email, email)

        # clear character - should show required message
        node.send_keys(Keys.BACKSPACE)
        self.assertInvalid(fg_username, node, 'required')
        self.assertInvalid(fg_username, domain, 'required')
        self.assertNotValidated(fg_email, email)

        # second character - node is now valid
        node.send_keys('ab')
        self.wait_for_valid(node)
        self.wait_for_valid(domain)
        self.assertValid(fg_username, node)
        self.assertValid(fg_username, domain)
        self.assertNotValidated(fg_email, email)

        node.send_keys(Keys.BACKSPACE)
        node.send_keys(Keys.BACKSPACE)
        self.wait_for_invalid(node)
        self.assertInvalid(fg_username, node, 'required')
        self.assertInvalid(fg_username, domain, 'required')
        self.assertNotValidated(fg_email, email)

        node.send_keys('exist')
        self.wait_for_valid(node)
        self.wait_for_valid(domain)
        self.assertValid(fg_username, node)
        self.assertValid(fg_username, domain)
        self.assertNotValidated(fg_email, email)

        # now node is "exists", and exists@example.com exists
        node.send_keys('s')
        self.wait_for_invalid(node)
        self.wait_for_invalid(domain)
        self.assertInvalid(fg_username, node, 'unique')
        self.assertInvalid(fg_username, domain, 'unique')
        self.assertNotValidated(fg_email, email)

        # select a different domain: makes it valid again (user doesn't exist elsewhere)
        sel = Select(domain)
        sel.select_by_value('example.net')
        self.wait_for_valid(node)
        self.wait_for_valid(domain)
        self.assertValid(fg_username, node)
        self.assertValid(fg_username, domain)
        self.assertNotValidated(fg_email, email)

        # select previous domain - makes it invalid again
        sel.select_by_value('example.com')
        self.wait_for_invalid(node)
        self.wait_for_invalid(domain)
        self.assertInvalid(fg_username, node, 'unique')
        self.assertInvalid(fg_username, domain, 'unique')
        self.assertNotValidated(fg_email, email)

        # Lets add an invalid character
        node.send_keys('@')
        self.assertInvalid(fg_username, node, 'invalid')
        self.assertInvalid(fg_username, domain, 'invalid')
        self.assertNotValidated(fg_email, email)

        # Remove @, means we have a collision again
        node.send_keys(Keys.BACKSPACE)

        # NOTE: This one is *nasty* because the element briefly is valid (until the JS callback
        #       returns that the element doesn't exist). But the transition never completes. So we have a
        #       manual wait to test that the error message is visible.
        self.wait_for_display(fg_username.find_element_by_css_selector('.invalid-feedback.invalid-unique'))

        # we still have to wait for invalid, because the visibility of the error message only means that the
        # callback returned, the CSS transition is still happening.
        self.wait_for_invalid(node)
        self.wait_for_invalid(domain)
        self.assertInvalid(fg_username, node, 'unique')
        self.assertInvalid(fg_username, domain, 'unique')

        # Add a space, makes it invalid
        node.send_keys(' ')
        self.assertInvalid(fg_username, node, 'invalid')
        self.assertInvalid(fg_username, domain, 'invalid')
        self.assertNotValidated(fg_email, email)

        # select different domain - and we're still invalid
        sel = Select(domain)
        sel.select_by_value('example.net')
        self.assertInvalid(fg_username, node, 'invalid')
        self.assertInvalid(fg_username, domain, 'invalid')
        self.assertNotValidated(fg_email, email)

        # Remove space, this makes it valid ("exists@example.net")
        node.send_keys(Keys.BACKSPACE)
        self.wait_for_valid(node)
        self.wait_for_valid(domain)
        self.assertValid(fg_username, node)
        self.assertValid(fg_username, domain)

        # Select example.com again, which means it's a collision
        sel.select_by_value('example.com')
        self.wait_for_invalid(node)
        self.wait_for_invalid(domain)
        self.assertInvalid(fg_username, node, 'unique')
        self.assertInvalid(fg_username, domain, 'unique')

    def test_async_validation(self):
        # create a test user so we can test for colisions.
        User.objects.create(username='exists@example.com')

        self.selenium.get('%s%s' % (self.live_server_url, reverse('account:register')))

        fg_username = self.find('#fg_username')
        node = self.selenium.find_element_by_id('id_username_0')
        domain = self.selenium.find_element_by_id('id_username_1')
        node.send_keys('exists')
        node.send_keys(' ')
        self.assertInvalid(fg_username, node, 'invalid')

        # now try the same by changing the domain
        node.send_keys(Keys.BACKSPACE)
        self.wait_for_display(fg_username.find_element_by_css_selector('.invalid-feedback.invalid-unique'))

        sel = Select(domain)
        sel.select_by_value('example.net')  # user does not exists with this domain
        node.send_keys('@')
        self.assertInvalid(fg_username, node, 'invalid')
