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

from django.conf import settings
from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from jsonfield import JSONField

from composite_field.l10n import LocalizedCharField as _LocalizedCharField
from composite_field.l10n import LocalizedTextField as _LocalizedTextField

from .constants import TARGET_MODEL
from .constants import TARGET_NAMED_URL
from .constants import TARGET_URL
from .formfields import LinkTargetField

LANGUAGES = [l[0] for l in getattr(settings, 'LANGUAGES', [])]


class LocalizedCharField(_LocalizedCharField):
    # see: https://bitbucket.org/bikeshedder/django-composite-field/pull-requests/6/map-returns-a-generator-in-py3-that-is/diff
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('languages', LANGUAGES)
        super(LocalizedCharField, self).__init__(*args, **kwargs)


class LocalizedTextField(_LocalizedTextField):
    # see: https://bitbucket.org/bikeshedder/django-composite-field/pull-requests/6/map-returns-a-generator-in-py3-that-is/diff
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('languages', LANGUAGES)
        super(LocalizedTextField, self).__init__(*args, **kwargs)


class LinkTargetDict(dict):
    @property
    def href(self):
        typ = int(self.get('typ', TARGET_URL))

        if typ == TARGET_URL:
            return self.get('url', '')
        elif typ == TARGET_NAMED_URL:
            return reverse(self['name'], *self['args'], **self['kwargs'])
        elif typ == TARGET_MODEL:
            ct = ContentType.objects.get_for_id(self['content_type'])
            obj = ct.get_object_for_this_type(pk=self['object_id'])
            return obj.get_absolute_url()
        return ''


class LinkTarget(JSONField):
    """Subclass of a JSONField to contain all relevant data to link to various objects.

    A JSONField is a model field that dynamically serializes its data to JSON.

    This field should store structured data that can be reconstructed to a link. When deserialized,
    it returns LinkTargetDict instead of just a dict, to provide the ``href`` property.
    Consequently, you can use this field in templates::

        <a href="{{ object.link_target.href }}">...</a>

    .. seealso:: https://github.com/bradjasper/django-jsonfield
    """
    def pre_init(self, value, obj):
        return LinkTargetDict(super(LinkTarget, self).pre_init(value, obj))

    def formfield(self, **kwargs):
        widget = kwargs.get('widget')
        admin = False
        if widget and issubclass(widget, AdminTextareaWidget):
            admin = True

        return LinkTargetField(admin=admin)
