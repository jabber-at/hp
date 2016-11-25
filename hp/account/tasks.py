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

from datetime import timedelta
from urllib.error import URLError

from celery import shared_task
from celery.utils.log import get_task_logger
from gpgmime.django import gpg_backend

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import constants as messages
from django.utils import translation
from django.utils.translation import ugettext as _
from django_xmpp_backends import backend

from core.models import Address
from core.utils import format_timedelta
from core.tasks import activate_language

from .models import Confirmation
from .models import UserLogEntry
from .constants import PURPOSE_SET_EMAIL

User = get_user_model()
log = get_task_logger(__name__)


@shared_task(bind=True)
@activate_language
def add_gpg_key_task(self, user_pk, address, language, fingerprint=None, key=None):
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

    user = User.objects.get(pk=user_pk)

    try:
        user.add_gpg_key(keys=key, fingerprint=fingerprint, language=language, address=address)
    except URLError as e:
        retries = self.request.retries
        if retries == self.max_retries:
            msg = _(
                'Could not reach keyserver. This was our final attempt. Giving up and sending '
                'mail unencrypted. Sorry.')
            log.exception(e)
            user.message(messages.ERROR, msg)

        delta = timedelta(seconds=60)
        delta_formatted = format_timedelta(delta)

        log.info('This is %s of %s tries.', self.request.retries, self.max_retries)
        msg = _('Could not reach keyserver. '
                'Will try again in %(time)s (%(retry)s of %(max_retries)s tries)') % {
                    'time': delta_formatted,
                    'retry': retries + 1,
                    'max_retries': self.max_retries,
        }
        user.message(messages.ERROR, msg)
        self.retry(exc=e, countdown=delta.seconds)


@shared_task(bind=True)
@activate_language
def send_confirmation_task(self, user_pk, to, purpose, language, address=None, **payload):
    user = User.objects.get(pk=user_pk)
    if address is not None:
        address = Address.objects.get_or_create(address=address)[0]

    conf = Confirmation.objects.create(user=user, purpose=purpose, language=language, to=to,
                                       address=address, payload=payload)
    conf.send()


@shared_task
@activate_language
def set_email_task(user_pk, to, language, address, fingerprint=None, key=None, **payload):
    """A custom task because we might need to send the email with a custom set of GPG keys."""

    user = User.objects.get(pk=user_pk)
    address = Address.objects.get_or_create(address=address)[0]

    if key:
        payload['gpg_recv_pub'] = key
    elif fingerprint:
        payload['gpg_recv_fp'] = fingerprint  # just so we know what was submitted
        payload['gpg_recv_pub'] = gpg_backend.fetch_key('0x%s' % fingerprint).decode('utf-8')
    else:
        payload['gpg_recv_pub'] = None  # do not encrypt

    with translation.override(language):
        conf = Confirmation.objects.create(user=user, purpose=PURPOSE_SET_EMAIL, language=language,
                                           to=to, address=address, payload=payload)
        conf.send()


@shared_task
def resend_confirmations(*conf_pks):
    """Task to resend the passed confirmation keys.

    Usage::

        # Resend confirmation keys with primary keys 3, 5 and 10:
        >>> resend_confirmations.delay(3, 5, 10)
    """
    for pk in conf_pks:
        conf = Confirmation.objects.get(pk=pk)
        conf.send()


@shared_task
def cleanup():
    UserLogEntry.objects.expired().delete()
    Confirmation.objects.expired().delete()

    # Remove users that are gone from the real XMPP server
    for hostname in settings.XMPP_HOSTS:
        existing_users = set([u.lower() for u in backend.all_users(hostname)])

        if len(existing_users) < 50:
            # A safety check if the backend for some reason does not return any users and does not
            # raise an exception.
            log.info('Skipping %s: Only %s users received.', hostname, len(existing_users))
            continue

        count = 0
        for user in User.objects.exclude(is_superuser=True).has_no_confirmations().host(hostname):
            username = user.node.lower()
            if username not in existing_users:
                log.info('%s: Remove user (gone from backend).', user.username)
                user.delete()
                count += 1

        log.info('%s: Removed %s users.', hostname, count)
