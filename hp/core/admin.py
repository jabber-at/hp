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
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from mptt.admin import DraggableMPTTAdmin

from .forms import MenuItemAdminForm
from .models import Address
from .models import AddressActivity
from .models import MenuItem

User = get_user_model()


class BaseModelAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        fields = list(super(BaseModelAdmin, self).get_readonly_fields(request, obj=obj))

        if obj is not None:
            if 'updated' not in fields:
                fields.append('updated')
            if 'created' not in fields:
                fields.append('created')
        return fields

    def get_fields(self, request, obj=None):
        fields = list(super(BaseModelAdmin, self).get_fields(request, obj=obj))

        if obj is not None:
            if 'updated' not in fields:
                fields.append('updated')
            if 'created' not in fields:
                fields.append('created')

        return fields


@admin.register(MenuItem)
class MenuItemAdmin(DraggableMPTTAdmin):
    form = MenuItemAdminForm
    list_display = (
        'tree_actions',
        'indented_title',
    )
    list_display_links = (
        'indented_title',
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('address', 'count_activities', 'count_confirmations', 'timerange', )
    search_fields = ['address']

    def get_queryset(self, request):
        qs = super(AddressAdmin, self).get_queryset(request)
        # NOTE: We add ordering here because the system check framework checks that each name given
        #       in the "ordering" class property is actually a model field.
        return qs.count_activities().count_confirmations()\
            .first_activity().last_activity().order_by('-count_activities')

    def timerange(self, obj):
        if obj.count_activities <= 1:
            return '-'
        diff = obj.last_activity - obj.first_activity
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        obj.timerange = diff

        return '%s days, %s:%s:%s' % (diff.days, hours, minutes, seconds)
    timerange.short_description = _('Timerange of activities')

    def count_activities(self, obj):
        return obj.count_activities
    count_activities.short_description = _('Number of activities')
    count_activities.admin_order_field = 'count_activities'

    def count_confirmations(self, obj):
        return obj.count_confirmations
    count_confirmations.short_description = _('Number of confirmations')
    count_confirmations.admin_order_field = 'count_confirmations'


@admin.register(AddressActivity)
class AddressActivityAdmin(admin.ModelAdmin):
    list_filter = ('activity', )
    list_display = ('address', 'activity', 'user', 'note', 'timestamp', )
    list_select_related = ('user', 'address', )
    ordering = ('-timestamp', )
    search_fields = ['user__username', 'address__address', 'note', ]
