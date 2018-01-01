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

import logging

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Certificate

log = logging.getLogger(__name__)


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ['hostname', 'hostnames', ],
        }),
        (_('Details'), {
            'fields': ['key_size', ('valid_from', 'valid_until', ), ],
        }),
        (_('Identifiers'), {
            'fields': ['serial', 'sha1', 'sha256', 'sha512', 'tlsa', ],
        }),
        (_('Certificate'), {
            'fields': ['pem', ],
        }),
    )
    readonly_fields = [
        'key_size', 'valid_from', 'valid_until', 'serial', 'sha1', 'sha256', 'sha512', 'tlsa', 'hostnames',
    ]

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (None, {
                    'fields': ['hostname', 'pem', ],
                }),
            )
        return super().get_fieldsets(request, obj=obj)
