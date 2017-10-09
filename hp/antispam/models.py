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

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel

from .querysets import BlockedQuerySet


def _default_email_timeout():
    if settings.BLOCKED_EMAIL_TIMEOUT is None:
        return None
    return timezone.now() + settings.BLOCKED_EMAIL_TIMEOUT


def _default_ipaddress_timeout():
    if settings.BLOCKED_IPADDRESS_TIMEOUT is None:
        return None
    return timezone.now() + settings.BLOCKED_IPADDRESS_TIMEOUT


class BlockedMixin(object):
    @property
    def is_blocked(self):
        return self.timeout > timezone.now()


class BlockedEmail(BlockedMixin, BaseModel):
    objects = BlockedQuerySet.as_manager()

    address = models.EmailField(unique=True)
    timeout = models.DateTimeField(default=_default_email_timeout)


class BlockedIpAddress(BlockedMixin, BaseModel):
    objects = BlockedQuerySet.as_manager()

    address = models.GenericIPAddressField(unique=True)
    timeout = models.DateTimeField(default=_default_ipaddress_timeout)
