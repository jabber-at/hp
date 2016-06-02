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
# If not, see <http://www.gnu.org/licenses/

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    readonly_fields = ('author', 'created', 'updated', )

    fieldsets = (
        (None, {
            'fields': ('author', 'created', 'updated', ),
        }),
        (_('Title'), {
            'fields': [('title_de', 'title_en'), ],
        }),
        (_('Text'), {
            'fields': [('text_de', 'text_en'), ],
        }),
    )

    def save_model(self, request, obj, form, change):
        print(change)
        if change is False:  # adding a new object
            obj.author = request.user
            obj.save()
