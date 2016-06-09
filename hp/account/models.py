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
from django_xmpp_backends.models import XmppBackendUser

from .constants import REGISTRATION_CHOICES
from .managers import UserManager


class User(XmppBackendUser, PermissionsMixin):
    # NOTE: MySQL only allows a 255 character limit
    jid = models.CharField(max_length=255, unique=True, verbose_name='JID')
    email = models.EmailField(null=True, blank=True)
    gpg_fingerprint = models.CharField(max_length=40, null=True, blank=True)

    # when the account was first registered
    registered = models.DateTimeField(auto_now_add=True)
    registration_method = models.SmallIntegerField(choices=REGISTRATION_CHOICES)

    # when the email was confirmed
    confirmed = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'jid'
    REQUIRED_FIELDS = ('email', )

    @property
    def node(self):
        return self.jid.split('@', 1)[0]

    @property
    def domain(self):
        return self.jid.split('@', 1)[1]

    @property
    def is_staff(self):
        return self.is_superuser

    def __str__(self):
        return self.jid
