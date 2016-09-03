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

import json

from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from account.models import GpgKey

User = get_user_model()


class Command(BaseCommand):
    """

    Create userdata dump with::

        python manage.py export > userdata.json
    """
    help = "Import a Drupal data export."
    _link_cache = None

    def add_arguments(self, parser):
        parser.add_argument('input', help="Path to input file.")

    def parse_timestamp(self, stamp):
        return timezone.make_aware(datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S'))

    def handle(self, input, **kwargs):
        with open(input) as stream:
            userdata = json.load(stream)

        User.objects.all().delete()

        for data in userdata:
            self.stdout.write(data['username'])
            self.stdout.flush()
            user = User(
                username=data['username'],
                email=data['email'],
                registration_method=data['registration_method'],
            )

            user._meta.get_field('registered').auto_now_add = False
            user.registered = self.parse_timestamp(data['registered'])
            if data.get('confirmed'):
                user.confirmed = self.parse_timestamp(data['confirmed'])

            user.save()

            if data.get('gpg_key'):
                with user.gpg_keyring(init=False) as backend:
                    fp = backend.import_key(data['gpg_key'].encode('utf-8'))
                    if fp != [data['gpg_fingerprint']]:
                        raise ValueError(fp, data['gpg_fingerprint'])
                    expires = backend.expires(fp[0])

                if expires is not None:
                    expires = timezone.make_aware(expires)
                GpgKey.objects.create(user=user, fingerprint=fp[0], key=data['gpg_key'],
                                      expires=expires)

        # Make users superuser
        User.objects.filter(
            username__in=['mati@jabber.at', 'astra@jabber.at']).update(is_superuser=True)
