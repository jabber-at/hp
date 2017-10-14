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

from .utils import normalize_email


class BlockedBaseManager(models.Manager):
    def block(self, address):
        """Block the passed address."""

        expires = self.get_expires()

        obj, created = self.get_or_create(address=address)
        if created is False:
            if obj.expires is None:
                return obj  # address is blocked indefinitely already
            elif expires is None:
                obj.expires = expires  # block indefinitely now
            else:
                obj.expires = max(expires, obj.expires)
            obj.save()

        return obj


class BlockedEmailManager(BlockedBaseManager):
    def get_expires(self):
        if settings.BLOCKED_EMAIL_TIMEOUT is not None:
            return timezone.now() + settings.BLOCKED_EMAIL_TIMEOUT

    def block(self, address):
        """Block the passed email address."""

        address = normalize_email(address)
        return super(BlockedEmailManager, self).block(address)


class BlockedIpAddressManager(BlockedBaseManager):
    def get_expires(self):
        if settings.BLOCKED_IPADDRESS_TIMEOUT is not None:
            return timezone.now() + settings.BLOCKED_IPADDRESS_TIMEOUT
