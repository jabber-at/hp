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

from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import ugettext_lazy as _

from django_xmpp_backends.models import XmppBackendUser

from core.models import Confirmation

from .constants import REGISTRATION_CHOICES
from .constants import REGISTRATION_WEBSITE
from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_SET_EMAIL
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_DELETE
from .managers import UserManager


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

    @property
    def is_staff(self):
        return self.is_superuser

    def __str__(self):
        return self.username


class AccountConfirmation(Confirmation):
    class Meta:
        proxy = True

    def send(self, request, user, purpose, **kwargs):
        node, domain = user.get_username().split('@', 1)
        subject = PURPOSES[purpose]['subject'] % {
            'domain': domain,
        }
        return super(AccountConfirmation, self).send(request, user, purpose, subject, **kwargs)
