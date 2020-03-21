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

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import BlockedEmail
from .models import BlockedIpAddress
from .utils import normalize_email


class ExpiredFilter(admin.SimpleListFilter):
    title = _('still valid bans')
    parameter_name = 'expired'

    def lookups(self, request, model_admin):
        return (
            ('0', _('Expired')),
            ('1', _('Still valid')),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == '0':
            return queryset.filter(expires__lt=now)
        elif self.value() == '1':
            return queryset.exclude(expires__lt=now)
        return queryset


@admin.register(BlockedEmail)
class BlockedEmailAdmin(admin.ModelAdmin):
    list_display = ['address', 'created', 'expires']
    list_filter = [ExpiredFilter]
    search_fields = ['address']

    def save_model(self, request, obj, form, change):
        obj.address = normalize_email(obj.address)
        return super(BlockedEmailAdmin, self).save_model(request, obj, form, change)


@admin.register(BlockedIpAddress)
class BlockedIpAddressAdmin(admin.ModelAdmin):
    list_display = ['address', 'created', 'expires']
    list_filter = [ExpiredFilter]
    search_fields = ['address']
