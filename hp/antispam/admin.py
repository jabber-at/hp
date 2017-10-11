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
# If not, see <http://www.gnu.org/licenses/.

from django.contrib import admin

from .models import BlockedEmail
from .models import BlockedIpAddress
from .utils import normalize_email


@admin.register(BlockedEmail)
class BlockedEmailAdmin(admin.ModelAdmin):
    list_display = ['address', 'created', 'expires']

    def save_model(self, request, obj, form, change):
        obj.address = normalize_email(obj.address)
        return super(BlockedEmailAdmin, self).save_model(request, obj, form, change)


@admin.register(BlockedIpAddress)
class BlockedIpAddressAdmin(admin.ModelAdmin):
    list_display = ['address', 'created', 'expires']
