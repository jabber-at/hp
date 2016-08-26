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

from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _

from django_xmpp_backends.models import XmppBackendUser
from jsonfield import JSONField
from gpgmime.django import gpg_backend

from core.models import BaseModel

from .constants import REGISTRATION_CHOICES
from .constants import REGISTRATION_WEBSITE
from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_SET_EMAIL
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_DELETE
from .managers import UserManager
from .managers import ConfirmationManager
from .querysets import ConfirmationQuerySet


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

    def add_gpg_key(self, request, form):

        if not form.cleaned_data.get('gpg_fingerprint') and not 'gpg_key' in request.FILES:
            return

        home = tempfile.mkdtemp()
        try:
            with gpg_backend.settings(home=home) as backend:
                if form.cleaned_data.get('gpg_fingerprint'):
                    key = gpg_backend.fetch_key('0x%s' % form.cleaned_data['gpg_fingerprint'])
                elif 'gpg_key' in request.FILES:
                    path = request.FILES['gpg_key'].temporary_file_path()
                    with open(path, 'rb') as stream:
                        key = stream.read()

                fp = backend.import_key(key)
                expires = backend.expires(fp)

                return GpgKey.objects.create(fingerprint=fp, key=key, expires=expires)
        finally:
            shutil.rmtree(home)

    def gpg_options(self, request):
        """Get keyword arguments suitable to pass to Confirmation.send()."""

        if not getattr(settings, 'GPG', True):
            return {}
        opts = {}

        if self.gpg_fingerprint:
            opts['gpg_encrypt'] = self.gpg_fingerprint

            # add the option to sign confirmations if the current site has a GPG fingerprint
            if request.site.get('GPG_FINGERPRINT'):
                opts['gpg_sign'] = request.site['GPG_FINGERPRINT']

        return opts

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
        text_template = Template(self.payload['text_template'])
        html_template = Template(self.payload['html_template'])
        subject = self.SUBJECTS[self.payload]

        context = {
            'user': self.user,
            'expires': self.expires,
        }

        text = text_template.render(context)
        html = html_template.render(context)

        self.purpose = purpose
        node, domain = user.get_username().split('@', 1)
        subject = PURPOSES[purpose]['subject'] % {
            'domain': domain,
        }
        return super(Confirmation, self).send(request, user, purpose, subject, **kwargs)


class UserLogEntry(BaseModel):
    """A model that logs user activity, e.g. a change of password or GPG key."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='log_entries')
    address = models.GenericIPAddressField()
    message = models.TextField()

    class Meta:
        verbose_name = 'User activity log'
        verbose_name_plural = 'User activity logs'

    def __str__(self):
        return '%s: %s' % (self.user, self.message)


class GpgKey(BaseModel):
    """A GPG key."""

    # NOTE: the fingerprint is *not* unique, because a key might be used for multiple accounts
    fingerprint = models.CharField(max_length=40)
    key = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='gpg_keys')

    class Meta:
        verbose_name = 'GPG key'
        verbose_name_plural = 'GPG keys'

    def __str__(self):
        return self.fingerprint
