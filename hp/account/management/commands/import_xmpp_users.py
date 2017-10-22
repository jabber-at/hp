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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from xmpp_backends.django import xmpp_backend
from xmpp_backends.base import UserNotFound

from ...constants import REGISTRATION_INBAND

User = get_user_model()


class Command(BaseCommand):
    help = 'Import existing users from the XMPP server.'

    def handle(self, *args, **kwargs):
        for domain in settings.XMPP_HOSTS:
            self.stdout.write('Importing users from %s.' % domain)
            created = 0

            users = xmpp_backend.all_users(domain)
            for node in users:
                username = '%s@%s' % (node, domain)

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    created += 1
                    try:
                        last_activity = xmpp_backend.get_last_activity(node, domain)
                    except UserNotFound:
                        last_activity = timezone.now()

                    user = User(
                        username=username,
                        registration_method=REGISTRATION_INBAND,
                        created_in_backend=True,
                        last_activity=last_activity,
                    )
                    user.save()

            self.stdout.write(self.style.SUCCESS('Imported %s/%s users.' % (created, len(users))))
