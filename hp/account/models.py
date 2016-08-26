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

from contextlib import contextmanager

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.template import Template
from django.template.loaders.base.Loader import get_template
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from django_xmpp_backends.models import XmppBackendUser
from jsonfield import JSONField
from gpgmime.django import gpg_backend
from gpgmime.django import GpgEmailMessage

from core.models import BaseModel

from .constants import PURPOSE_DELETE
from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_SET_EMAIL
from .constants import REGISTRATION_CHOICES
from .constants import REGISTRATION_WEBSITE
from .managers import ConfirmationManager
from .managers import UserManager
from .querysets import ConfirmationQuerySet
from .querysets import GpgKeyQuerySet


PURPOSES = {
    PURPOSE_REGISTER: {
        'subject': _('Your new account on %(domain)s'),
    },
    PURPOSE_SET_EMAIL: {
        'subject': _('Confirm the email address for your %(domain)s account'),
    },
    PURPOSE_RESET_PASSWORD: {
        'subject': _('Reset the password for your %(domain)s account'),
    },
    PURPOSE_DELETE: {
        'subject': _('Delete your account on %(domain)s'),
    },
}
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
    email = models.EmailField(null=True, blank=True, verbose_name=_('Email'))
    gpg_fingerprint = models.CharField(max_length=40, null=True, blank=True)

    # when the account was first registered
    registered = models.DateTimeField(auto_now_add=True)
    registration_method = models.SmallIntegerField(
        default=REGISTRATION_WEBSITE, choices=REGISTRATION_CHOICES)

    # when the email was confirmed
    confirmed = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

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

    def log(self, address, message):
        self.log_entries.create(address=address, message=message)

    @contextmanager
    def gpg_keyring(self, init=True):
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
        """
        home = tempfile.mkdtemp()
        try:
            with gpg_backend.settings(home=home) as backend:
                if init is True:  # import existing valid gpg keys
                    for key in self.gpg_keys.filter(expires__gt=timezone.now()):
                        backend.import_key(key)

                yield backend
        finally:
            shutil.rmtree(home)

    def add_gpg_key(self, keys, fingerprint, language, address):
        if fingerprint:
            keys = gpg_backend.fetch_key('0x%s' % fingerprint)  # fetch key from keyserver
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
                    with translation.override(language):
                        self.log(_('Error importing GPG key.'))
                    raise

        for key, fp, expires in imported:
            expires = timezone.make_aware(expires)

            # Create or update the GPG key
            dbkey, created = GpgKey.objects.update_or_create(
                user=self, fingerprint=fp, defaults={'key': key, 'expires': expires, })

            with translation.override(language):
                if created is True:
                    message = _('Added GPG key 0x%s.') % fp
                else:
                    message = _('Updated GPG key 0x%s.') % fp

            self.log(address=address, message=message)
        return GpgKey.objects.create(fingerprint=fp, key=key, expires=expires)

    def __str__(self):
        return self.username


class Confirmation(BaseModel):
    objects = ConfirmationManager.from_queryset(ConfirmationQuerySet)

    key = models.CharField(max_length=40, default=default_key)
    expires = models.DateTimeField(default=default_expires)
    purpose = models.CharField(null=True, blank=True, max_length=16)
    payload = JSONField(default=default_payload)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='confirmations')

    SUBJECTS = {
        PURPOSE_REGISTER: _('Your new account on {{ user.domain }}'),
    }

    def send(self):
        subject = Template(self.SUBJECTS[self.payload])
        text_template = get_template(self.payload['text_template'])
        html_template = get_template(self.payload['html_template'])

        context = {
            'user': self.user,
            'expires': self.expires,
        }

        with translation.override(self.payload['language']):
            subject = subject.render(context)
            text = text_template.render(context)
            html = html_template.render(context)

        frm = self.payload['from']
        to = self.payload['to']

        msg = GpgEmailMessage(subject, text, frm, [to])
        msg.attach_alternative(html, 'text/html')
        msg.send()


class UserLogEntry(BaseModel):
    """A model that logs user activity, e.g. a change of password or GPG key."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='log_entries')
    # TODO: Address should be nullable in case admin does something in the admin interface
    address = models.GenericIPAddressField()
    message = models.TextField()

    class Meta:
        verbose_name = 'User activity log'
        verbose_name_plural = 'User activity logs'

    def __str__(self):
        return '%s: %s' % (self.user, self.message)


class GpgKey(BaseModel):
    """A GPG key."""

    objects = GpgKeyQuerySet.as_manager()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='gpg_keys')

    # NOTE: the fingerprint is *not* unique, because a key might be used for multiple accounts
    fingerprint = models.CharField(max_length=40)
    key = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)
    # TODO: add revoked flag

    class Meta:
        # TODO: user and fingerprint should be unique_together
        verbose_name = 'GPG key'
        verbose_name_plural = 'GPG keys'

    def __str__(self):
        return self.fingerprint
