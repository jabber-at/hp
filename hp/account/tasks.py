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

import logging
import shutil
import tempfile

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import translation
from django.utils.translation import ugettext as _
from gpgmime.django import gpg_backend

from .models import GpgKey
from .models import UserLogEntry

User = get_user_model()
log = logging.getLogger()


@shared_task
def add_gpg_key(user_pk, address, language, fp, key):
    user = User.objects.get(pk=user_pk)

    if fp:
        key = gpg_backend.fetch_key('0x%s' % fp)
    else:
        key = key.encode('utf-8')  # we need bytes to import

    home = tempfile.mkdtemp()
    try:
        with gpg_backend.settings(home=home) as backend:
            fprs = backend.import_key(key)
            for fpr in fprs:
                log.info('%s: Add GPG key %s.', user.username, fpr)
                expires = backend.expires(fpr)

                # TODO: This currently stores all keys if the user submitted multiple keys ("key"
                #       is directly from the uploaded form)
                GpgKey.objects.create(user=user, fingerprint=fpr, key=key, expires=expires)

                # TODO: This currently is always English, language is not yet passed.
                with translation.override(language):
                    UserLogEntry.objects.create(user=user, address=address,
                                                message=_('Added GPG key 0x%s.') % fpr)
    finally:
        shutil.rmtree(home)
