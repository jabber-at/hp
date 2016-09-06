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
# You should have received a copy of the GNU General Public License along with django-xmpp-account.
# If not, see <http://www.gnu.org/licenses/>.


from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from django_xmpp_backends import backend

User = get_user_model()


class Command(BaseCommand):
    """Update all users that exist on the server with the created_in_backend flag.

    This is a temporary command to introduce the created_in_backend flag to existing users.
    """

    help = "Update all users that exist on the server with the created_in_backend flag."

    def handle(self, **kwargs):
        for host, config in settings.XMPP_HOSTS.items():
            users = ['%s@%s' % (u, host) for u in backend.all_users(host)]
            count = User.objects.filter(username__in=users).update(created_in_backend=True)
            self.stdout.write('Updated %s users for %s' % (count, host))

