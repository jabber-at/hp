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

import inspect

from datetime import timedelta
from functools import wraps

from celery import shared_task
from celery.utils.log import get_task_logger
from gpgliblib.django import GpgEmailMessage

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils import translation
from .models import Address
from .models import AddressActivity
from .models import CachedMessage
from .utils import load_contact_keys

from xmpp_http_upload.models import Upload

User = get_user_model()
log = get_task_logger(__name__)


def activate_language(task, language_param='language'):
    """Decorator for tasks that activates the language passed to it.

    Decorate a task that accepts the ``language`` parameter to automatically activate the passed
    language for this task. For example, given the task::

        from django.utils.translation import ugettext as _

        @shared_task
        @activate_language
        def my_task(language):
            log.info(_('Text in English'))

    ... will output the text in the language passed to it (assuming you have created the propper
    translations, of course.

    Parameters
    ----------

    language_param : str, optional
        Name of the language parameter used to pass the language.
    """
    def _decorator(*args, **kwargs):
        sig = inspect.signature(task)
        bound = sig.bind(*args, **kwargs)

        # Requires Python 3.5
        #bound.apply_defaults()

        # Find out if any language was passed to the task
        old_language = None
        language = None
        if language_param in sig.parameters:
            # TODO/NOTE: Might not work if default is used (see apply_defaults above)
            language = bound.arguments[language_param]

        try:
            if language is not None:
                old_language = translation.get_language()
                translation.activate(language)

            return task(*args, **kwargs)
        finally:
            # Reactivate old language
            if language is not None:
                translation.activate(old_language)

    return wraps(task)(_decorator)


@shared_task
def send_contact_email(hostname, subject, message, recipient=None, user_pk=None, address=None):
    if not recipient and not user_pk:
        raise ValueError("Need at least recipient or user")

    host = settings.XMPP_HOSTS[hostname]
    from_email = host.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
    recv_fps = None
    recipient_list = [host['CONTACT_ADDRESS']]

    # We add the connecting IP-Address and the user (if any).
    headers = {
        'X-Homepage-Submit-Address': address,
    }

    if user_pk is None:
        reply_to = [recipient, host['CONTACT_ADDRESS']]
    else:
        user = User.objects.get(pk=user_pk)
        recipient_list.append(user.email)
        reply_to = [user.email, host['CONTACT_ADDRESS']]
        recv_fps = list(user.gpg_keys.valid().values_list('fingerprint', flat=True))
        headers['X-Homepage-Logged-In-User'] = user

    # If we have a GPG fingerprint for the user AND we have fingerprints for the contact addresses,
    # we use GPG.
    if recv_fps and host.get('CONTACT_GPG_FINGERPRINTS'):
        contact_fps = load_contact_keys(hostname)
        recv_fps += contact_fps.keys()
        sign_fp = host.get('GPG_FINGERPRINT')

        with user.gpg_keyring(default_trust=True, hostname=hostname) as backend:
            for contact_key in contact_fps.values():
                backend.import_key(contact_key)

            msg = GpgEmailMessage(
                subject, message, from_email, recipient_list, reply_to=reply_to, headers=headers,
                gpg_backend=backend, gpg_recipients=recv_fps, gpg_signer=sign_fp)

            # Attach the users public key(s) as "key.asc" so we can reply encrypted.
            attachment = ''.join(user.gpg_keys.valid().values_list('key', flat=True))
            msg.attach('key.asc', attachment, 'text/gpg-key')

            msg.send()
    else:
        email = EmailMessage(subject, message, from_email, recipient_list, reply_to=reply_to,
                             headers=headers)
        email.send()


@shared_task
def cleanup():
    """Remove various accumulating data from the core app."""

    expired = timezone.now() - timedelta(days=31)
    AddressActivity.objects.filter(timestamp__lt=expired).delete()
    Address.objects.inactive().delete()
    CachedMessage.objects.filter(created__lt=expired).delete()

    # Cleanup XEP-0363 uploads
    Upload.objects.cleanup()
