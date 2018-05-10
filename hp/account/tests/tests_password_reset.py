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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from xmpp_backends.django import xmpp_backend

from core.tests.base import SeleniumTestCase

from ..constants import PURPOSE_RESET_PASSWORD
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


class RegisterSeleniumTests(SeleniumTestCase):
    def test_reset(self):
        """Test basic password reset."""

        self.selenium.get('%s%s' % (self.live_server_url, reverse('account:reset_password')))

        user = User.objects.create(
            username=JID, email=EMAIL, confirmed=timezone.now(), created_in_backend=True)
        xmpp_backend.create_user(NODE, DOMAIN, PWD)
        self.assertTrue(user.check_password(PWD))
        self.assertFalse(user.check_password(PWD2))

        #fg_username = self.find('#fg_username')
        node = self.selenium.find_element_by_id('id_username_0')

        node.send_keys(NODE)
        self.wait_for_valid_form()

        with self.mock_celery() as mocked, freeze_time(NOW_STR):
            self.selenium.find_element_by_css_selector('button[type="submit"]').click()
            self.wait_for_page_load()

        self.assertTaskCount(mocked, 1)

        site = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]
        self.assertTaskCall(
            mocked, send_confirmation_task,
            user_pk=user.pk, purpose=PURPOSE_RESET_PASSWORD, to=EMAIL, hostname=site['NAME'],
            base_url=self.live_server_url, language='en', address='127.0.0.1'
        )
        self.assertEqual(len(mail.outbox), 1)

        confirmation = Confirmation.objects.get(user=user, purpose=PURPOSE_RESET_PASSWORD)
        self.selenium.get('%s%s' % (self.live_server_url, confirmation.urlpath))
        self.wait_for_page_load()

        self.find('#id_new_password1').send_keys(PWD2)
        self.find('#id_new_password2').send_keys(PWD2)
        self.wait_for_valid_form()
        with freeze_time(NOW2_STR):
            self.find('button[type="submit"]').click()
            self.wait_for_page_load()

        # get user again
        user = User.objects.get(username='%s@%s' % (NODE, DOMAIN))
        # TODO: use freezegun for this
        #self.assertEqual(user.last_activity, NOW2)
        self.assertFalse(user.check_password(PWD))
        self.assertTrue(user.check_password(PWD2))
