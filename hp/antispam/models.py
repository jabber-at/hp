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
# You should have received a copy of the GNU General Public License along with this project.
# If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel

from .managers import BlockedEmailManager
from .managers import BlockedIpAddressManager
from .querysets import BlockedEmailQuerySet
from .querysets import BlockedQuerySet


def _default_email_expires():
    if settings.BLOCKED_EMAIL_TIMEOUT is None:
        return None
    return timezone.now() + settings.BLOCKED_EMAIL_TIMEOUT


def _default_ipaddress_expires():
    if settings.BLOCKED_IPADDRESS_TIMEOUT is None:
        return None
    return timezone.now() + settings.BLOCKED_IPADDRESS_TIMEOUT


class BlockedMixin(object):
    def __str__(self):
        return 'Blocked: %s' % self.address

    @property
    def is_blocked(self):
        return self.expires > timezone.now()


class BlockedEmail(BlockedMixin, BaseModel):
    objects = BlockedEmailManager.from_queryset(BlockedEmailQuerySet)()

    address = models.EmailField(unique=True, help_text=_('The blocked email address'))
    expires = models.DateTimeField(
        default=_default_email_expires, null=True, blank=True,
        help_text=_('When this block expires. If not set, it never expires.'))

    class Meta:
        verbose_name = _('Blocked email address')
        verbose_name_plural = _('Blocked email addresses')


class BlockedIpAddress(BlockedMixin, BaseModel):
    objects = BlockedIpAddressManager.from_queryset(BlockedQuerySet)()

    address = models.GenericIPAddressField(unique=True, help_text=_('The blocked IP address'))
    expires = models.DateTimeField(
        default=_default_ipaddress_expires, null=True, blank=True,
        help_text=_('When this block expires. If not set, it never expires.'))

    class Meta:
        verbose_name = _('Blocked IP address')
        verbose_name_plural = _('Blocked IP addresses')
