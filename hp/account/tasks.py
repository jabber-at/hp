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

import socket
from datetime import date
from datetime import timedelta
from urllib.error import URLError

from celery import Task
from celery import shared_task
from celery.utils.log import get_task_logger
from gpgliblib.django import gpg_backend

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import constants as messages
from django.urls import reverse
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from xmpp_backends.base import UserNotFound
from xmpp_backends.django import xmpp_backend

from core.models import Address
from core.utils import format_timedelta
from core.tasks import activate_language

from .models import Confirmation
from .models import UserLogEntry
from .constants import PURPOSE_SET_EMAIL

User = get_user_model()
log = get_task_logger(__name__)


class FetchKeyTask(Task):
    """A base class that handles fetching GPG keys."""

    def fetch_key(self, fingerprint, user):
        """Fetch given GPG key.

        This function will retry the task if fetching fails and inform the user of any errors.
        If the final retry fails (or an error not related to fetching the key is raised), the
        function does not handle the exception.

        Parameters
        ----------

        fingerprint : str
        user : User
            The user to logg error messages to.
        """
        try:
            return gpg_backend.fetch_key('0x%s' % fingerprint).decode('utf-8')
        except (URLError, socket.timeout) as e:
            retries = self.request.retries

            # Log exception using standard logging
            log.info('Failed fetching key %s: %s/%s tries', fingerprint, retries, self.max_retries)
            log.exception(e)

            delta = timedelta(seconds=60 * 10)

            if retries == self.max_retries:
                msg = ugettext_noop(
                    'Unable to fetch GPG key. Giving up and sending mail unencrypted. Sorry.')
                user.log(msg)
                user.message(messages.ERROR, msg)
                raise

            else:
                delta_formatted = format_timedelta(delta)
                payload = {
                    'max': self.max_retries + 1,
                    'retry': retries + 1,
                    'time': delta_formatted,
                }
                msg = ugettext_noop(
                    'Unable to fetch GPG key (%(retry)s of %(max)s tries). '
                    'Will try again in %(time)s.')

                user.log(msg, **payload)
                user.message(messages.ERROR, msg, **payload)
                self.retry(exc=e, countdown=delta.seconds)


@shared_task(bind=True, base=FetchKeyTask)
def add_gpg_key_task(self, user_pk, address, fingerprint=None, key=None):
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
    if not fingerprint and not key:
        log.error('Neither fingerprint nor key passed.')
        return

    user = User.objects.get(pk=user_pk)

    # Fetch key if we just get the fingerprint
    if not key and fingerprint:
        try:
            key = self.fetch_key(fingerprint, user)
        except (URLError, socket.timeout) as e:
            return

    user.add_gpg_key(keys=key, fingerprint=fingerprint, address=address)


@shared_task(bind=True)
@activate_language
def send_confirmation_task(self, user_pk, to, purpose, language, address=None, **payload):
    user = User.objects.get(pk=user_pk)
    if address is not None:
        address = Address.objects.get_or_create(address=address)[0]

    conf = Confirmation.objects.create(user=user, purpose=purpose, language=language, to=to,
                                       address=address, payload=payload)
    conf.send()


@shared_task(bind=True, base=FetchKeyTask)
@activate_language
def set_email_task(self, user_pk, to, language, address, fingerprint=None, key=None, **payload):
    """A custom task because we might need to send the email with a custom set of GPG keys."""

    user = User.objects.get(pk=user_pk)
    address = Address.objects.get_or_create(address=address)[0]

    if key:
        payload['gpg_recv_pub'] = key
    elif fingerprint:
        try:
            payload['gpg_recv_pub'] = self.fetch_key(fingerprint, user)
            payload['gpg_recv_fp'] = fingerprint  # just so we know what was submitted
        except (URLError, socket.timeout) as e:
            payload['gpg_recv_pub'] = False  # do not encrypt
    else:
        payload['gpg_recv_pub'] = False  # do not encrypt

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
def update_last_activity(random_update=50):
    # Update some random users with recent activity so we have at least a vague picture of
    # how recent users are active.
    for user in User.objects.order_by('?').not_expiring()[:random_update]:
        try:
            last_activity = xmpp_backend.get_last_activity(user.node, user.domain)
        except UserNotFound:
            log.warn('%s: User not found in XMPP backend.', user)
            continue

        if last_activity is None:
            log.warn('%s: Could not get last activity.', user)
            continue

        user.last_activity = timezone.make_aware(last_activity)
        user.save()

    # Update last activity of users with more then 350 days of inactivity
    for user in User.objects.select_related('notifications').expiring():
        log.debug('%s: Updating last activity.', user)

        try:
            last_activity = xmpp_backend.get_last_activity(user.node, user.domain)
        except UserNotFound:
            log.warn('%s: User not found in XMPP backend.', user)
            continue

        if last_activity is None:
            # This may happen when the user was already deleted in the backend (handled by cleanup)
            log.warn('%s: Could not get last activity.', user)
            continue

        log.debug('%s: Updated last_activity from %s to %s.', user, user.last_activity,
                  last_activity)
        user.last_activity = timezone.make_aware(last_activity)
        notifs = user.notifications

        # On what date the user will be removed and how many days this is from now
        when = user.last_activity.date() + settings.ACCOUNT_EXPIRES_DAYS
        delta = when - date.today()

        # If the updated last_activity still isn't more recent, the user requested a notification
        # and has a confirmed email address, we send a mail to the user.
        if user.is_confirmed and user.is_expiring and notifs.account_expires and \
                notifs.account_expires_notified is False and delta > timedelta():
            log.debug('%s: Notifying user at %s', user, user.email)

            host = settings.XMPP_HOSTS[user.domain]
            base_url = host['CANONICAL_BASE_URL'].rstrip('/')

            context = {  # NOQA
                'domain': user.domain,
                'expires_days': settings.ACCOUNT_EXPIRES_DAYS.days,
                'host': host,
                'jid': user.username,
                'login_url': '%s%s' % (base_url, reverse('account:login')),
                'password_url': '%s%s' % (base_url, reverse('account:reset_password')),
                'user': user,
                'when': when,
                'when_days': delta.days,
            }

            log.info('%s: Sending expiration notice to %s.', user, user.email)
            with translation.override(user.default_language):
                subject = _('Your account on {{ domain }} is about to expire')
                user.send_mail_template('account/email/user_expires', context, subject)

            notifs.account_expires_notified = True
            notifs.save()

        user.save()


@shared_task
def cleanup():
    UserLogEntry.objects.expired().delete()
    Confirmation.objects.expired().delete()

    # Remove users that are gone from the real XMPP server
    for hostname in settings.XMPP_HOSTS:
        existing_users = set([u.lower() for u in xmpp_backend.all_users(hostname)])

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
