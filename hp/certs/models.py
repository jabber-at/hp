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

import binascii

import pytz
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtensionOID

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from core.models import BaseModel

from .querysets import CertificateQuerySet
from .utils import add_colons
from .utils import format_general_name
from .utils import int_to_hex


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
    md5 = models.CharField(max_length=47, blank=True, verbose_name='MD5')
    sha1 = models.CharField(max_length=59, blank=True, verbose_name='SHA-1')
    sha256 = models.CharField(max_length=95, blank=True, verbose_name='SHA-256')
    sha512 = models.CharField(max_length=191, blank=True, verbose_name='SHA-512')

    objects = CertificateQuerySet.as_manager()
    _x509 = None

    def __str__(self):
        return '%s: %s' % (self.hostname, self.serial)

    def save(self, *args, **kwargs):
        # auto-compute values from certificate
        self.hostnames = self.get_hostnames()
        self.key_size = self.x509.public_key().key_size
        self.valid_from = pytz.utc.localize(self.x509.not_valid_before)
        self.valid_until = pytz.utc.localize(self.x509.not_valid_after)

        self.serial = int_to_hex(self.x509.serial_number)
        self.md5 = self.get_digest(hashes.MD5())
        self.sha1 = self.get_digest(hashes.SHA1())
        self.sha256 = self.get_digest(hashes.SHA256())
        self.sha512 = self.get_digest(hashes.SHA512())

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('certs:cert-id', kwargs={
            'hostname': self.hostname,
            'date': self.valid_from.date(),
        })

    ###############################
    # Cryptography helper methods #
    ###############################
    # These methods are copied from django-ca (https://django-ca.readthedocs.io/), which is by the same author
    # as this model.

    @property
    def x509(self):
        if self._x509 is None:
            backend = default_backend()
            self._x509 = x509.load_pem_x509_certificate(self.pem.encode(), backend)
        return self._x509

    def get_digest(self, algo):
        return add_colons(binascii.hexlify(self.x509.fingerprint(algo)).upper().decode('utf-8'))

    def get_hostnames(self):
        try:
            ext = self.x509.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        except x509.ExtensionNotFound:
            return []

        return [format_general_name(name) for name in ext.value]
