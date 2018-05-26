# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

from django.db import models
from django.utils import timezone


class CertificateQuerySet(models.QuerySet):
    def enabled(self):
        return self.filter(enabled=True)

    def hostname(self, hostname):
        return self.filter(hostname=hostname)

    def valid(self, now=None):
        if now is None:
            now = timezone.now()

        return self.filter(valid_from__lt=now, valid_until__gt=now)

    def newest(self):
        return self.order_by('-valid_from')
