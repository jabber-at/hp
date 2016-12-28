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

from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.contrib.messages import constants as messages
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template import Context
from django.template import Template
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils import translation
from django.utils.crypto import get_random_string
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _

from gpgmime.django import GpgEmailMessage
from gpgmime.django import gpg_backend
from jsonfield import JSONField
from xmpp_backends.django import xmpp_backend
from xmpp_backends.django.models import XmppBackendUser

from core.models import Address
from core.models import BaseModel
from core.models import CachedMessage
from core.utils import load_private_key

from .constants import PURPOSE_DELETE
from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_SET_EMAIL
from .constants import REGISTRATION_CHOICES
from .constants import REGISTRATION_WEBSITE
from .managers import UserManager
from .managers import UserLogEntryManager
from .querysets import ConfirmationQuerySet
from .querysets import GpgKeyQuerySet
from .querysets import UserLogEntryQuerySet
from .querysets import UserQuerySet


log = logging.getLogger(__name__)
_gpg_key_delimiter = b"""-----END PGP PUBLIC KEY BLOCK-----
-----BEGIN PGP PUBLIC KEY BLOCK-----"""


def default_key():
    salt = get_random_string(32)
    value = get_random_string(64)
    return salted_hmac(salt, value).hexdigest()


def default_expires():
    return timezone.now() + settings.USER_CONFIRMATION_TIMEOUT


def default_payload():
    return {}


class User(XmppBackendUser, PermissionsMixin):
    # NOTE: MySQL only allows a 255 character limit
    username = models.CharField(max_length=255, unique=True, verbose_name=_('Username'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))

    # when the account was first registered
    registered = models.DateTimeField(auto_now_add=True)
    registration_method = models.SmallIntegerField(
        default=REGISTRATION_WEBSITE, choices=REGISTRATION_CHOICES)

    # when the email was confirmed
    confirmed = models.DateTimeField(null=True, blank=True)

    # If the user is created in the backend (not necessarily the same as confirmed, old users don't
    # have an email address).
    created_in_backend = models.BooleanField(default=False)

    # If the user is blocked.
    blocked = models.BooleanField(default=False)

    # When the user last logged in.
    last_activity = models.DateTimeField(default=timezone.now)

    objects = UserManager.from_queryset(UserQuerySet)()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('email', )

    def clean(self):
        self.username = self.username.lower()
        return super(User, self).clean()

    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        return super(User, self).save(*args, **kwargs)

    @property
    def is_staff(self):
        return self.is_superuser

    @property
    def is_confirmed(self):
        return self.email and self.confirmed

    @property
    def is_expiring(self):
        return self.last_activity < timezone.now() - settings.ACCOUNT_EXPIRES_NOTIFICATION_DAYS

    def log(self, message, address=None, **kwargs):
        self.log_entries.create(message=message, address=address, payload=kwargs)

    def message(self, level, message):
        return CachedMessage.objects.create(user=self, level=level, message=message)

    def logs(self):
        return self.log_entries.order_by('-created')

    def uses_gpg(self):
        return self.gpg_keys.valid().exists()

    def block(self):
        self.blocked = True
        self.save()
        self.log('You have been blocked. Sorry.')
        xmpp_backend.block_user(username=self.node, domain=self.domain)

    @contextmanager
    def gpg_keyring(self, init=True, hostname=None, **kwargs):
        """Context manager that yields a temporary GPG keyring.

        To avoid any locking issues and to isolate the GPG keys for users, every operation that
        interacts with gpg (and thus uses the keyring) is with a separate, temporary keyring that
        is created specifically for the operations.

        Example::

            user = User.objects.get(username='user@example.com')
            with user.gpg_keyring() as backend:
                backend.import_key(...)

        Parameters
        ----------

        init : bool, optional
            If ``False``, do not import existing (valid) keys into the keyring.
        hostname : str, optional
            If set, also import the private key for the given host configured in the ``XMPP_HOSTS``
            setting.
        """
        home = tempfile.mkdtemp()
        if hostname is not None:
            host_fp, host_key, host_pub = load_private_key(hostname)

        try:
            with gpg_backend.settings(home=home, **kwargs) as backend:
                if init is True:  # import existing valid gpg keys
                    for key in self.gpg_keys.valid():
                        backend.import_key(key.key.encode('utf-8'))

                if hostname is not None:
                    backend.import_private_key(host_key)
                    backend.import_key(host_pub)

                yield backend
        finally:
            shutil.rmtree(home)

    def add_gpg_key(self, keys, fingerprint, language, address):
        if fingerprint:
            kwargs = {}
            if settings.GPG_KEYSERVER:
                kwargs['keyserver'] = settings.GPG_KEYSERVER

            # Fetch key from keyserver
            keys = gpg_backend.fetch_key('0x%s' % fingerprint, **kwargs)
        elif isinstance(keys, str):
            keys = keys.encode('utf-8')  # convert to bytes

        imported = []

        with self.gpg_keyring(init=False) as backend:
            for key in keys.split(_gpg_key_delimiter):
                try:
                    fp = backend.import_key(keys)[0]
                    expires = backend.expires(fp)
                    imported.append((key, fp, expires))
                except Exception:
                    err = _('Error importing GPG key.')
                    self.log(err, address=address)  # log entry in "Recent activity"
                    self.message(messages.ERROR, err)  # message to user
                    raise

        for key, fp, expires in imported:
            if expires:  # None if the key does not expire
                expires = timezone.make_aware(expires)

            # Create or update the GPG key
            dbkey, created = GpgKey.objects.update_or_create(
                user=self, fingerprint=fp, defaults={'key': key, 'expires': expires, })

            if created is True:
                message = _('Added GPG key 0x%(fingerprint)s.') % {'fingerprint': fp, }
            else:
                message = _('Updated GPG key 0x%(fingerprint)s.') % {'fingerprint': fp, }

            self.log(address=address, message=message)
            self.message(messages.INFO, message)

    def send_mail(self, subject, message, html_message, host=None, gpg_key=None):
        """Send an email to the user.

        Parameters
        ----------

        subject : str
            The subject to use.
        message : str
            The email message in plain text format.
        html_message : str
            The email message in html format.
        host : str, optional
            The XMPP_HOST configuration to use getting from-address and signing GPG keys. Defaults
            to the domain-part of the username.

            .. TODO:: Check if this parameter is really necessary.

        gpg_key : bytes or False, optional
            A bytestring to use as a GPG key instead of any key set for the user. Pass ``False`` to
            send a plaintext email even if the user has GPG keys defined.
        """
        if host is None:
            host = settings.XMPP_HOSTS[self.domain]
        frm = host['DEFAULT_FROM_EMAIL']
        keys = list(self.user.gpg_keys.valid().values_list('fingerprint', flat=True))

        if gpg_key is not False or keys:
            sign_fp = host.get('GPG_FINGERPRINT')

            with self.gpg_keyring(default_trust=True, hostname=host['NAME']) as backend:
                if gpg_key:
                    log.info('Imported custom keys.')
                    keys = backend.import_key(gpg_key)

                msg = GpgEmailMessage(subject, message, frm, [self.email],
                                      gpg_backend=backend, gpg_recipients=keys, gpg_signer=sign_fp)
                msg.attach_alternative(html_message, 'text/html')
                msg.send()
        else:
            msg = EmailMultiAlternatives(subject, message, frm, [self.email])
            msg.attach_alternative(html_message, 'text/html')
            msg.send()

    def __str__(self):
        return self.username


class Notifications(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
        related_name='notifications')

    account_expires = models.BooleanField(default=True, help_text=_(
        'Send user an email when the account is about to be deleted.'))
    account_expires_notified = models.BooleanField(default=False)
    gpg_expires = models.BooleanField(default=True, help_text=_(
        'Send user an email when his GPG key is about to expire.'))
    gpg_expires_notified = models.BooleanField(default=False)


class Confirmation(BaseModel):
    objects = ConfirmationQuerySet.as_manager()

    # NOTE: This is *not* necessarily the same as the email address of the user (a new address
    #       might have been added).
    to = models.EmailField(blank=True, verbose_name=_('Recipient'))

    key = models.CharField(max_length=40, default=default_key)
    expires = models.DateTimeField(default=default_expires)
    purpose = models.CharField(max_length=16)
    payload = JSONField(default=default_payload)

    # NOTE: Do not add choices here, or changing settings.LANGUAGES will trigger a migration
    language = models.CharField(max_length=2)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='confirmations')
    address = models.ForeignKey(Address, models.PROTECT, blank=True, null=True,
                                related_name='confirmations')

    SUBJECTS = {
        PURPOSE_DELETE: _('Delete your account on {{ user.domain }}'),
        PURPOSE_REGISTER: _('Your new account on {{ user.domain }}'),
        PURPOSE_RESET_PASSWORD: _('Reset your password on {{ user.domain }}'),
        PURPOSE_SET_EMAIL: _('Confirm new email address for your {{ user.domain }} account'),
    }

    def send(self):
        hostname = self.payload['hostname']
        host = settings.XMPP_HOSTS[hostname]
        path = reverse('account:%s_confirm' % self.purpose, kwargs={'key': self.key})

        context = {
            'domain': self.user.domain,
            'expires': self.expires,
            'jid': self.user.get_username(),
            'node': self.user.node,
            'user': self.user,
            'uri': '%s%s' % (self.payload['base_url'], path),
        }

        with translation.override(self.language):
            subject = Template(self.SUBJECTS[self.purpose]).render(Context(context))

            context['subject'] = subject
            text = render_to_string('account/confirm/%s.txt' % self.purpose, context)
            html = render_to_string('account/confirm/%s.html' % self.purpose, context)

        frm = host['DEFAULT_FROM_EMAIL']

        custom_key = self.payload.get('gpg_recv_pub')  # key from the payload

        # Only use the GPG keys stored for the user if the payload does not explicity specify
        # a GPG key to use.  This is used e.g. when the user sets an email address and wants to use
        # a different GPG key or none at all.
        keys = None
        if 'gpg_recv_pub' not in self.payload:
            keys = list(self.user.gpg_keys.valid().values_list('fingerprint', flat=True))

        if custom_key or keys:
            sign_fp = host.get('GPG_FINGERPRINT')

            with self.user.gpg_keyring(default_trust=True, hostname=hostname) as backend:
                if custom_key:
                    log.info('Imported custom keys.')
                    keys = backend.import_key(custom_key.encode())

                msg = GpgEmailMessage(subject, text, frm, [self.to],
                                      gpg_backend=backend, gpg_recipients=keys, gpg_signer=sign_fp)
                msg.attach_alternative(html, 'text/html')
                msg.send()
        else:
            msg = EmailMultiAlternatives(subject, text, frm, [self.to])
            msg.attach_alternative(html, 'text/html')
            msg.send()


class UserLogEntry(BaseModel):
    """A model that logs user activity, e.g. a change of password or GPG key."""

    objects = UserLogEntryManager.from_queryset(UserLogEntryQuerySet)()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='log_entries')
    address = models.GenericIPAddressField(null=True, blank=True)
    message = models.TextField()
    payload = JSONField(default=default_payload)

    class Meta:
        verbose_name = 'User activity log'
        verbose_name_plural = 'User activity logs'

    @property
    def localized(self):
        return _(self.message) % self.payload

    def __str__(self):
        return self.message % self.payload


class GpgKey(BaseModel):
    """A GPG key."""

    objects = GpgKeyQuerySet.as_manager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='gpg_keys')

    # NOTE: the fingerprint is *not* unique, because a key might be used for multiple accounts
    fingerprint = models.CharField(max_length=40)
    key = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)

    def refresh(self):
        # TODO: Add ability to override keyserver with setting
        refetched = gpg_backend.fetch_key('0x%s' % self.fingerprint)

        with self.user.gpg_keyring(init=False) as backend:
            backend.import_key(refetched)
            expires = backend.expires(self.fingerprint)

        # TODO: No way of knowing if the key is revoked, so we don't set it yet
        self.expires = timezone.make_aware(expires)
        self.save()

    class Meta:
        unique_together = ('user', 'fingerprint')
        verbose_name = 'GPG key'
        verbose_name_plural = 'GPG keys'

    def __str__(self):
        return self.fingerprint


@receiver(post_save, sender=User)
def create_notifications(sender, instance, created, **kwargs):
    if created:
        Notifications.objects.create(user=instance)
