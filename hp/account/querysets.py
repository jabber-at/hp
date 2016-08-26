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
from django.utils import timezone


class GpgKeyQuerySet(models.QuerySet):
    def valid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__gte=now)

    def invalid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__lt=now)


class ConfirmationQuerySet(models.QuerySet):
    def purpose(self, purpose):
        return self.filter(purpose=purpose)

    def valid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__gte=now)

    def expired(self, now=None):
        if now is None:
            now = timezone.now()

        return self.filter(expires__lt=now)
