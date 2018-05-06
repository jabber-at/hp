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

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from core.tests.base import TestCase
from core.tests.base import SeleniumTestCase

from ..tasks import send_confirmation_task


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


class RegisterSeleniumTests(SeleniumTestCase):
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
        print(node.get_attribute('value'))
        self.wait_for_invalid(node)
        self.wait_for_invalid(domain)
        self.assertInvalid(fg_username, node, 'unique')
        self.assertInvalid(fg_username, domain, 'unique')
