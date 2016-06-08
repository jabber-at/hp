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
from django.db import models
from django.utils.translation import ugettext_lazy as _

from jsonfield import JSONField

from composite_field import CompositeField
from composite_field.l10n import LocalizedCharField as _LocalizedCharField
from composite_field.l10n import LocalizedTextField as _LocalizedTextField

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


class LinkTarget(CompositeField):
    TARGET_URL = 0
    TARGET_NAMED_URL = 1
    TARGET_PAGE = 2
    TARGET_BLOGPOST = 3

    TARGET_CHOICES = {
        TARGET_URL: _('URL'),
        TARGET_NAMED_URL: _('Named URL'),
        TARGET_PAGE: _('Page'),
        TARGET_BLOGPOST: _('Blog Post'),
    }

    type = models.SmallIntegerField(choices=sorted(TARGET_CHOICES.items(), key=lambda k: k[0]))
    target = models.CharField(max_length=255, help_text=_('Link target'))
    params = JSONField(default={})
