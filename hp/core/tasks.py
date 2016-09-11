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

from celery import shared_task
from celery.utils.log import get_task_logger
from gpgmime.django import GpgEmailMessage

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.utils import timezone
from .models import Address
from .models import AddressActivity
from .models import CachedMessage
from .utils import load_private_key
from .utils import load_contact_keys

from xmpp_http_upload.models import Upload

User = get_user_model()
log = get_task_logger(__name__)


@shared_task
def error():
    log.error("Error test by mati")
    raise Exception("Exception raised by mati")


@shared_task
def send_contact_email(domain, subject, message, recipient=None, user=None, address=None):
    if not recipient and not user:
        raise ValueError("Need at least recipient or user")

    config = settings.XMPP_HOSTS[domain]
    from_email = config.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
    gpg_recipients = None
    recipient_list = [config['CONTACT_ADDRESS']]

    if user is None:
        reply_to = [recipient, config['CONTACT_ADDRESS']]
    else:
        user = User.objects.get(pk=user)
        recipient_list.append(user.email)
        reply_to = [user.email, config['CONTACT_ADDRESS']]
        gpg_recipients = list(user.gpg_keys.valid().values_list('fingerprint', flat=True))

    # We add the connecting IP-Address and the user (if any).
    headers = {
        'X-Homepage-Logged-In-User': user,
        'X-Homepage-Submit-Address': address,
    }

    # If we have a GPG fingerprint for the user AND we have fingerprints for the contact addresses,
    # we use GPG.
    if gpg_recipients and config.get('CONTACT_GPG_FINGERPRINTS'):
        gpg_signer, sign_key = load_private_key(domain)
        contact_gpg_recipients = load_contact_keys(domain)
        gpg_recipients += contact_gpg_recipients.keys()

        with user.gpg_keyring(default_trust=True) as backend:
            if sign_key:  # import private key for signing
                backend.import_private_key(sign_key)

            for contact_key in contact_gpg_recipients.values():  #
                backend.import_key(contact_key)

            msg = GpgEmailMessage(
                subject, message, from_email, recipient_list, reply_to=reply_to, headers=headers,
                gpg_backend=backend, gpg_recipients=gpg_recipients, gpg_signer=gpg_signer)

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
