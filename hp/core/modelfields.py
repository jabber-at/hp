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

import logging

from django.contrib.admin.widgets import AdminTextareaWidget
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from composite_field.l10n import LocalizedCharField as _LocalizedCharField
from composite_field.l10n import LocalizedTextField as _LocalizedTextField
from jsonfield import JSONField

from .constants import TARGET_MODEL
from .constants import TARGET_NAMED_URL
from .constants import TARGET_URL
from .formfields import LinkTargetField

log = logging.getLogger(__name__)


class LocalizedCharField(_LocalizedCharField):
    many_to_many = None


class LocalizedTextField(_LocalizedTextField):
    many_to_many = None


class LinkTargetDict(dict):
    _content_type = None

    def validate(self):
        """Validate that this object points to a valid object."""

        typ = int(self.get('typ', TARGET_URL))

        if typ == TARGET_URL:
            if not self.get('url'):
                raise ValidationError('URL must not be empty.')
        elif typ == TARGET_NAMED_URL:
            try:
                reverse(self['name'], *self['args'], **self['kwargs'])
            except Exception as e:
                raise ValidationError('%s: %s' % (type(e).__name__, e))
        elif typ == TARGET_MODEL:
            try:
                ct = ContentType.objects.get_for_id(self['content_type'])
                ct.get_object_for_this_type(pk=self['object_id'])
            except Exception as e:
                raise ValidationError('%s: %s' % (type(e).__name__, e))

    @property
    def content_type(self):
        if self._content_type is None:
            try:
                self._content_type = ContentType.objects.get_for_id(self['content_type'])
            except ContentType.DoesNotExist:
                log.warn('ContentType with id %s not found.', self['content_type'])
                self._content_type = False
        return self._content_type

    def warm_cache(self):
        typ = int(self.get('typ', TARGET_URL))
        if typ == TARGET_MODEL:
            self.content_type

    @property
    def menu_key(self):
        typ = int(self.get('typ', TARGET_URL))

        if typ == TARGET_NAMED_URL:
            return self['name'], tuple(self['args']), self['kwargs']
        elif typ == TARGET_MODEL:
            ct = self.content_type
            if not ct:
                return ''
            return '%s_%s:%s' % (ct.app_label, ct.model, self['object_id'])

    @property
    def href(self):
        typ = int(self.get('typ', TARGET_URL))

        if typ == TARGET_URL:
            return self.get('url', '')
        elif typ == TARGET_NAMED_URL:
            try:
                return reverse(self['name'], *self['args'], **self['kwargs'])
            except NoReverseMatch as e:
                log.exception(e)
                return ''
        elif typ == TARGET_MODEL:
            ct = self.content_type
            if not ct:
                return ''
            obj = ct.get_object_for_this_type(pk=self['object_id'])
            if hasattr(obj, 'get_absolute_url'):
                return obj.get_absolute_url()
            else:
                log.warn('%s: Model has no get_absolute_url()', obj._meta.label)
                return ''

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
        value = LinkTargetDict(super(LinkTarget, self).pre_init(value, obj))
        if type(value) == dict:
            value = LinkTargetDict(value)
        return value

    def from_db_value(self, *args, **kwargs):
        value = super().from_db_value(*args, **kwargs)
        if type(value) == dict:
            value = LinkTargetDict(value)
        return value

    def to_python(self, value):
        value = super(LinkTarget, self).to_python(value)
        if type(value) == dict:
            value = LinkTargetDict(value)
        return value

    def formfield(self, **kwargs):
        widget = kwargs.get('widget')
        admin = False
        if widget and issubclass(widget, AdminTextareaWidget):
            admin = True

        return LinkTargetField(admin=admin)
