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

from django import forms
from django.contrib import admin

from mptt.admin import DraggableMPTTAdmin

from .models import Page
from .models import MenuItem
from .modelfields import LinkTarget
from .formfields import LinkTargetField


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    pass


class MenuItemAdminForm(forms.ModelForm):
    target = LinkTargetField()

    class Meta:
        fields = '__all__'
        model = MenuItem


@admin.register(MenuItem)
class MenuItemAdmin(DraggableMPTTAdmin):
    form = MenuItemAdminForm
    list_display = (
        'tree_actions',
        'indented_title',
        # ...more fields if you feel like it...
    )

#    formfield_overrides = {
#        LinkTarget: {
#            'widget': LinkTargetField,
#        },
#    }
    list_display_links = (
        'indented_title',
    )
