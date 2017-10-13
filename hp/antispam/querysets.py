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

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .utils import normalize_email


class BlockedQuerySet(models.QuerySet):
    def is_blocked(self, address):
        return self.filter(Q(expires__isnull=True) | Q(expires__gt=timezone.now()), address=address).exists()


class BlockedEmailQuerySet(BlockedQuerySet):
    def is_blocked(self, address):
        address = normalize_email(address)
        return super(BlockedEmailQuerySet, self).is_blocked(address)
