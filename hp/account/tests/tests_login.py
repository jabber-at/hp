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

from core.tests.base import TestCase

User = get_user_model()
NOW = datetime(2017, 4, 23, 11, 22, 33)
NOW_UTC = pytz.utc.localize(NOW)
NOW_STR = '2017-04-23 11:22:33+00:00'
NOW2 = datetime(2017, 4, 23, 12, 23, 34)
NOW2_UTC = pytz.utc.localize(NOW2)
NOW2_STR = '2017-04-23 12:23:34+00:00'

NODE = 'user'
DOMAIN = 'example.com'
JID = '%s@%s' % (NODE, DOMAIN)
EMAIL = 'user@example.com'
COMMON_PWD = 'password123'
PWD = 'GVIhRx5y3uH2'
PWD2 = 'oJsfiLCwshha'


class LoginTestCase(TestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.create(
            username=JID, email=EMAIL, confirmed=NOW_UTC, created_in_backend=True, last_activity=NOW_UTC)
        xmpp_backend.create_user(NODE, DOMAIN, PWD)
        xmpp_backend.set_last_activity(NODE, DOMAIN, timestamp=NOW)

        self.url = reverse('account:login')
        self.client = Client()

    def test_basic(self):
        self.assertEqual(xmpp_backend.get_last_activity(NODE, DOMAIN), NOW)

        with self.mock_celery() as mocked, freeze_time(NOW2_STR):
            post = self.client.post(self.url, {
                'username_0': NODE, 'username_1': DOMAIN, 'password': PWD,
            }, follow=True)

        self.assertNoTasks(mocked)
        self.assertFalse(post.context['user'].is_anonymous)
        self.assertEqual(post.status_code, 200)
        self.assertEqual(post.resolver_match.app_names, ['account'])
        self.assertEqual(post.resolver_match.url_name, 'detail')

        # Last activity gets updated on login
        self.assertEqual(xmpp_backend.get_last_activity(NODE, DOMAIN), NOW2)

    def test_failed_login(self):
        with self.mock_celery() as mocked, freeze_time(NOW2_STR):
            post = self.client.post(self.url, {
                'username_0': NODE, 'username_1': DOMAIN, 'password': PWD2,
            }, follow=True)

        self.assertNoTasks(mocked)
        self.assertTrue(post.context['user'].is_anonymous)
        self.assertEqual(post.resolver_match.app_names, ['account'])
        self.assertEqual(post.resolver_match.url_name, 'login')
        self.assertEqual(post.status_code, 200)

        # Last activity is NOT updated
        self.assertEqual(xmpp_backend.get_last_activity(NODE, DOMAIN), NOW)
        errors = [e.code for e in post.context['form'].non_field_errors().data]
        self.assertIn('invalid_login', errors)
