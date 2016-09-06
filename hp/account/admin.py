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

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import Confirmation
from .models import GpgKey
from .models import User
from .models import UserLogEntry


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'gpg_fingerprint'),
        }),
    )
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'registered', 'registration_method', 'confirmed',
                       'gpg_fingerprint'),
        }),
    )
    list_display = ('username', 'email', 'registered', 'confirmed', )
    list_filter = ('is_superuser', )
    ordering = ('-registered', )
    readonly_fields = ['username', 'registered', ]
    search_fields = ['username', 'email', ]


@admin.register(UserLogEntry)
class UserLogEntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created')
    ordering = ('-created', )


@admin.register(GpgKey)
class GpgKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'fingerprint', 'expires')
    list_select_related = ('user', )
    ordering = ('-created', )


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'address', 'purpose', 'to', 'expires', )
    list_filter = ('purpose', )
    list_select_related = ('user', 'address', )
    search_fields = ('key', 'to', 'user__username', 'user__email', )


admin.site.unregister(Group)
