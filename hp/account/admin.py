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

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('registered', )
    list_display = ('jid', 'email', 'registered', 'confirmed', )
    list_filter = ('is_superuser', )
    readonly_fields = ['registered', ]
    add_fieldsets = (
        (None, {
            'fields': ('jid', 'email', 'gpg_fingerprint'),
        }),
    )
    fieldsets = (
        (None, {
            'fields': ('jid', 'email', 'registered', 'registration_method', 'confirmed',
                       'gpg_fingerprint'),
        }),
    )

admin.site.unregister(Group)
