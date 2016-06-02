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

from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

from basedjango.models import BaseModel

from .modelfields import LocalizedCharField
from .modelfields import LocalizedTextField

class BasePage(BaseModel):
    title = LocalizedCharField(max_length=16, help_text=_('Page title'))
    text = LocalizedTextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    published = models.BooleanField(default=True, help_text=_(
        'Wether or not the page is public.'))

    class Meta:
        abstract = True


class Page(BasePage):
    def __str__(self):
        return self.title.current


class MenuItem(MPTTModel, BaseModel):
    title = LocalizedCharField(max_length=16, help_text=_('Page title'))
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def __str__(self):
        return self.title.current

    class MPTTMeta:
        order_insertion_by = ['title_en']
