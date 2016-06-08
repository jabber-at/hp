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

from jsonfield import JSONField

from composite_field.l10n import LocalizedCharField as _LocalizedCharField
from composite_field.l10n import LocalizedTextField as _LocalizedTextField

from .constants import TARGET_PAGE
from .constants import TARGET_URL

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
        elif typ == TARGET_PAGE:
            return '/page/%s' % self['page']
        return ''


class LinkTarget(JSONField):
    def to_python(self, value, obj):
        return LinkTargetDict(super(LinkTarget, self).pre_init(value, obj))

    def pre_init(self, value, obj):
        return LinkTargetDict(super(LinkTarget, self).pre_init(value, obj))
