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
from datetime import timedelta

import pytz
from freezegun import freeze_time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import get_language

from xmpp_backends.django import xmpp_backend

from core.models import Address
from core.tests.base import SeleniumTestCase
from core.tests.base import TestCase

from ..constants import PURPOSE_REGISTER
from ..models import Confirmation
from ..tasks import update_last_activity

User = get_user_model()

FORMAT = "%Y-%m-%d %H:%M:%S+00:00"
LAST_ACTIVITY_1 = pytz.utc.localize(datetime(2018, 1, 1, 0, 0, 0))
LAST_ACTIVITY_1_STR = LAST_ACTIVITY_1.strftime(FORMAT)
LAST_ACTIVITY_2 = pytz.utc.localize(datetime(2018, 3, 1, 0, 0, 0))
LAST_ACTIVITY_2_STR = LAST_ACTIVITY_1.strftime(FORMAT)
NOW_1 = pytz.utc.localize(datetime(2018, 4, 1, 0, 0, 0))
NOW_1_STR = NOW_1.strftime(FORMAT)
NOW_2 = pytz.utc.localize(datetime(2019, 2, 25, 0, 0, 0))
NOW_2_STR = NOW_2.strftime(FORMAT)
NOW_3 = pytz.utc.localize(datetime(2019, 3, 7, 0, 0, 0))
NOW_3_STR = NOW_3.strftime(FORMAT)

NODE = 'user'
DOMAIN = 'example.com'
JID = '%s@%s' % (NODE, DOMAIN)
EMAIL = 'user@example.com'
PWD = 'password123'
PWD2 = 'password456'


class AccountExpiresTestCase(TestCase):
    @override_settings(ACCOUNT_EXPIRES_NOTIFICATION_DAYS=timedelta(days=355),
                       ACCOUNT_EXPIRES_DAYS=timedelta(days=365))
    def test_expiring(self):
        # create user, also in backend
        user = User.objects.create(username=JID, email=EMAIL, created_in_backend=True,
                                   last_activity=LAST_ACTIVITY_1, confirmed=LAST_ACTIVITY_1)
        xmpp_backend.create_user(NODE, DOMAIN, PWD)
        xmpp_backend.set_last_activity(NODE, DOMAIN, timestamp=LAST_ACTIVITY_2)

        self.assertEqual(user.last_activity, LAST_ACTIVITY_1)

        with self.mock_celery() as mocked, freeze_time(NOW_1_STR):
            update_last_activity()

        user = User.objects.get(username=JID)
        self.assertTaskCount(mocked, 0)
        self.assertEqual(len(mail.outbox), 0)  # no mails where sent yet (user is not expiring)
        self.assertEqual(user.last_activity, LAST_ACTIVITY_2)  # new last activity from backend

        with self.mock_celery() as mocked, freeze_time(NOW_2_STR):
            self.assertTrue(user.is_expiring)
            self.assertTrue(user.notifications.account_expires)
            update_last_activity()

        self.assertTaskCount(mocked, 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(user.last_activity, LAST_ACTIVITY_2)  # last activity stays the same

        mail.outbox = []
        self.assertEqual(len(mail.outbox), 0)

        # run task the next day and make sure that no mail is sent
        with self.mock_celery() as mocked, freeze_time(NOW_2_STR):
            self.assertTrue(user.is_expiring)
            self.assertTrue(user.notifications.account_expires)
            update_last_activity()

        self.assertTaskCount(mocked, 0)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(user.last_activity, LAST_ACTIVITY_2)  # last activity stays the same
