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
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from composite_field.l10n import LocalizedField
from composite_field.base import CompositeField
from tinymce.widgets import TinyMCE

from core.admin import BaseModelAdmin

from .forms import BasePageAdminForm
from .models import BlogPost
from .models import Page

User = get_user_model()


class BasePageAdmin(BaseModelAdmin):
    actions = ['make_publish', 'make_unpublish']
    form = BasePageAdminForm
    formfield_overrides = {
        models.TextField: {
            'widget': TinyMCE(attrs={'cols': 80, 'rows': 20}, mce_attrs={
                'theme': "advanced",
            }),
        },
    }

    def get_fields(self, request, obj=None):
        fields = list(super(BasePageAdmin, self).get_fields(request, obj=obj))
        if obj is not None and 'author' not in fields:
            fields.append('author')
        return fields

    def get_action(self, action):
        func, act, desc = super(BasePageAdmin, self).get_action(action)

        if action in ['make_publish', 'make_unpublish']:
            context = {
                'models': self.model._meta.verbose_name_plural,
            }
            desc = desc % context

        return func, act, desc

    def _get_composite_field_tuple(self, fields):
        new_fields = []
        for name in fields:
            if not isinstance(name, str):  # don't handle tuples et al
                new_fields.append(name)
                continue

            field = self.model._meta.get_field(name)

            if isinstance(field, LocalizedField):
                new_fields.append(tuple([f.name for f in field.subfields.values()]))
            elif isinstance(field, CompositeField):
                new_fields += [f.name for f in field.subfields.values()]
            else:
                new_fields.append(name)
        return new_fields

    def _get_subfields(self, name):
        return tuple([f.name for f in self.model._meta.get_field(name).subfields.values()])

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(BasePageAdmin, self).get_fieldsets(request, obj=obj)

        if self.fieldsets is None and self.fields is None:
            # The ModelAdmin class doesn't set fields or fieldsets - we replace localized
            # fields with tuples.
            fields = []
            has_title = has_slug = has_text = False
            title_fields = self._get_subfields('title')
            slug_fields = self._get_subfields('slug')
            text_fields = self._get_subfields('text')
            for field in fieldsets[0][1]['fields']:
                if field in title_fields:
                    if has_title is False:
                        fields.append(title_fields)
                        has_title = True
                elif field in slug_fields:
                    if has_slug is False:
                        fields.append(slug_fields)
                        has_slug = True
                elif field in text_fields:
                    if has_text is False:
                        fields.append(text_fields)
                        has_text = True
                else:
                    fields.append(field)

            fieldsets[0][1]['fields'] = list(fields)
        else:
            # ModelAdmin sets fields or fieldsets. This means that e.g. 'title' should
            # be replaced with ('title_de', 'title_en').
            for name, options in fieldsets:
                options['fields'] = self._get_composite_field_tuple(options['fields'])

        return fieldsets

    def render_change_form(self, request, context, add, **kwargs):
        """Override to add javascript only when adding an object.

        It adds Javascript to dynamically calculate the slug of a BasePage object and set the field
        accordingly.

        Ordinarily you would add Javascript in a Media subclass, but then it would get *always*
        added. The form for adding/changing an object is identical, so there is no way to only
        act when adding a form (and you don't normally want to change existing slugs, since they're
        part of the URL).

        Also filters the users of the author field to admins, otherwise the select box would be too
        large.
        """

        qs = context['adminform'].form.fields['author'].queryset
        context['adminform'].form.fields['author'].queryset = qs.filter(is_superuser=True)

        if add:
            context['media'] += forms.Media(js=("core/js/basepage-add.js", ))
        return super(BasePageAdmin, self).render_change_form(request, context, add, **kwargs)

    def save_model(self, request, obj, form, change):
        if change is False:  # adding a new object
            obj.author = request.user
        obj.save()

    #################
    # Admin actions #
    #################
    def make_publish(self, request, queryset):
        queryset.update(published=True)
    make_publish.short_description = _('Publish selected %(models)s')

    def make_unpublish(self, request, queryset):
        queryset.update(published=False)
    make_unpublish.short_description = _('Unpublish selected %(models)s')

    class Media:
        css = {
            'all': ('blog/admin/css/basepage.css', ),
        }
        js = (
            'blog/admin/js/basepage.js',
        )


class AuthorFilter(admin.SimpleListFilter):
    title = _('Author')
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        qs = User.objects.annotate(num_posts=models.Count('blogpost')).filter(num_posts__gt=1)
        return [(u.pk, u.username) for u in qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(author_id=self.value())


@admin.register(BlogPost)
class BlogPostAdmin(BasePageAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'text'),
        }),
        (_('Descriptions'), {
            'fields': ('meta_summary', 'twitter_summary', 'opengraph_summary', 'html_summary', ),
            'description': _('<p>Descriptions are used by various systems (RSS readers, Facebook, '
                             '...) to generate previews of this content.</p>'
                             '<p><strong>NOTE:</strong> Longer variants fall back to shorter '
                             'variants if not set.</p>'),
            'classes': ('description', ),
        }),
        (_('Meta'), {
            'fields': (('published', 'sticky'), 'author', ),
        }),
    )
    list_display = ['__str__', 'created', ]
    list_filter = [AuthorFilter, 'published', 'sticky', ]
    ordering = ('-sticky', '-created', )
    search_fields = ['title_de', 'title_en', 'text_en', 'text_de']


@admin.register(Page)
class PageAdmin(BasePageAdmin):
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'text'),
        }),
        (_('Descriptions'), {
            'fields': ('meta_summary', 'twitter_summary', 'opengraph_summary', ),
            'description': _('<p>Descriptions are used by various systems (Facebook, '
                             '...) to generate previews of this content.</p>'
                             '<p><strong>NOTE:</strong> Longer variants fall back to shorter '
                             'variants if not set.</p>'),
            'classes': ('description', ),
        }),
        (_('Meta'), {
            'fields': ('published', 'author', ),
        }),
    )
    list_display = ['__str__', 'updated', ]
    list_filter = ['published', ]
    ordering = ('-title', )
    search_fields = ['title_de', 'title_en', 'text_en', 'text_de']
