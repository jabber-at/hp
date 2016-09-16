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

import os

import gnupg

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


class Command(BaseCommand):
    help = "Generate GnuPG key for a host given in XMPP_HOSTS in localsettings.py."

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--type', default='RSA', metavar='[DSA|RSA]',
            help='The type of primary key to generate (default: %(default)s).'),
        parser.add_argument(
            '-s', '--size', default=4096, type=int, metavar='BITS',
            help='The length of the primary key (default: %(default)s).'),
        parser.add_argument('--name', help="Override the real name (default: the xmpp-host used."),
        parser.add_argument(
            '-f', '--force', action='store_true', default=False,
            help="Force regeneration of GPG key."),
        parser.add_argument(
            '-q', '--quiet', action='store_true', default=False,
            help="Do not output deleted users."),
        parser.add_argument('host', help="The hostname to generate a GPG key for.")

    def handle(self, host, **kwargs):
        if settings.GNUPG is None:
            raise CommandError('GnuPG disabled by "GNUPG = None" in localsettings.py.')
        if host not in settings.XMPP_HOSTS:
            raise CommandError('%s: Host not named in XMPP_HOSTS setting.' % host)

        if not os.path.exists(settings.GNUPG['gnupghome']):
            os.makedirs(settings.GNUPG['gnupghome'], 0o700)

        # We create our own instance (and don't use settings.GPG) because it is not defined when
        # creating the first key.
        gpg = gnupg.GPG(**settings.GNUPG)

        # option sanitization
        if kwargs['name'] is None:
            kwargs['name'] = host
        kwargs['type'] = kwargs['type'].upper()

        if gpg is not None:
            fingerprint = settings.XMPP_HOSTS.get('GPG_FINGERPRINT')
            secret_keys = gpg.list_keys(secret=True)
            secret_fps = [k['fingerprint'] for k in secret_keys]

            if fingerprint and fingerprint in secret_fps and not kwargs['force']:
                raise CommandError('Fingerprint set and found, use --force to force regenration.')

        email = settings.XMPP_HOSTS[host].get('FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        self.stdout.write('Generating key for %s <%s>... (takes a long time!)' % (host, email))

        params = gpg.gen_key_input(
            key_length=kwargs['size'],
            key_type=kwargs['type'],
            name_real=kwargs['name'],
            name_comment='',
            name_email=email
        )
        key = gpg.gen_key(params)
        if key.fingerprint:
            self.stdout.write(
                'Fingerprint is "%s", add as "GPG_FINGERPRINT" to the XMPP_HOSTS entry.' %
                key.fingerprint)
        else:
            raise CommandError('Cannot generate key, gpg output was: %s' % key.stderr)

        dest_dir = settings.STATICFILES_DIRS[0]
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        export = gpg.export_keys(key.fingerprint)
        dest_path = os.path.join(dest_dir, '%s.asc' % key.fingerprint)
        with open(dest_path, 'w') as stream:
            stream.write(export)
        self.stdout.write(
            'Key exported to %s, use "manage.py collectstatic" to make the keys downloadable.'
            % dest_path)
