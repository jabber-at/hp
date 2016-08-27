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

from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils import translation

from .models import Confirmation

User = get_user_model()
log = get_task_logger(__name__)


@shared_task
def add_gpg_key_task(user_pk, address, language, fingerprint=None, key=None):
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
    with translation.override(language):
        user.add_gpg_key(keys=key, fingerprint=fingerprint, language=language, address=address)


@shared_task
def send_confirmation_task(user_pk, to, purpose, language, **payload):
    user = User.objects.get(pk=user_pk)
    conf = Confirmation.objects.create(user=user, purpose=purpose, language=language, to=to,
                                       payload=payload)
    conf.send()
