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
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from core.models import BaseModel


def _default_hostnames():
    return []


class Certificate(BaseModel):
    hostname = models.CharField(max_length=255, help_text=_('Primary hostname of this certificate.'))

    # raw certificate
    pem = models.TextField(help_text=_('Certificate, in PEM format.'))

    # key values
    hostnames = JSONField(default=_default_hostnames, blank=True)
    key_size = models.PositiveSmallIntegerField(blank=True)
    valid_from = models.DateTimeField(blank=True)
    valid_until = models.DateTimeField(blank=True)

    # identifiers
    serial = models.CharField(max_length=64, blank=True)
    sha1 = models.CharField(max_length=59, blank=True)
    sha256 = models.CharField(max_length=95, blank=True)
    sha512 = models.CharField(max_length=191, blank=True)

    # tlsa fingerprint (sha512)
    tlsa = models.CharField(max_length=191, blank=True)
