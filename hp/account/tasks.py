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

import shutil
import tempfile

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _
from gpgmime.django import gpg_backend

from .models import GpgKey
from .models import UserLogEntry

User = get_user_model()
log = get_task_logger(__name__)

# Delimiter to split uploaded key data with. A user might upload multiple keys.
_gpg_key_delimiter = b"""-----END PGP PUBLIC KEY BLOCK-----
-----BEGIN PGP PUBLIC KEY BLOCK-----"""


@shared_task
def add_gpg_key(user_pk, address, language, fingerprint=None, key=None):
    """Task to add or update a submitted GPG key.

    You need to pass either the fingerprint or the raw key. If neither is passed, the task will
    log an error.

    Parameters
    ----------

    user_pk : int
        Primary key of the user.
    address : str
        Address the change is originating from.
    language : str
        Language the user currently used.
    fingerprint : str, optional
        The full fingerprint to add (without a "0x" prefix).
    key : str, optional
        The key to add, in ASCII armored text format. This might include multiple keys.
    """
    if fingerprint is None and key is None:
        log.error('Neither fingerprint nor key passed.')
        return

    user = User.objects.get(pk=user_pk)

    if fingerprint:
        keys = gpg_backend.fetch_key('0x%s' % fingerprint)  # fetch key from keyserver
    else:
        keys = key.encode('utf-8')  # convert to bytes

    # Create a temporary gpg home directory to import keys.
    home = tempfile.mkdtemp()
    try:
        with gpg_backend.settings(home=home) as backend:
            for key in keys.split(_gpg_key_delimiter):
                fpr = backend.import_key(key)[0]
                log.info('%s: Add/update GPG key %s.', user.username, fpr)

                expires = backend.expires(fpr)
                if expires is not None:
                    expires = timezone.make_aware(expires)

                # Create or update the GPG key
                dbkey, created = GpgKey.objects.update_or_create(
                    user=user, fingerprint=fpr, defaults={
                        'key': key, 'fingerprint': fpr, 'expires': expires, })

                with translation.override(language):
                    if created is True:
                        message = _('Added GPG key 0x%s.') % fpr
                    else:
                        message = _('Updated GPG key 0x%s.') % fpr

                UserLogEntry.objects.create(user=user, address=address, message=message)
    finally:
        shutil.rmtree(home)
