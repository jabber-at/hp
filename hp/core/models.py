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

from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

#from composite_field.l10n import LocalizedCharField
#from composite_field.l10n import LocalizedTextField
from jsonfield import JSONField
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

from .constants import ACTIVITY_FAILED_LOGIN
from .constants import ACTIVITY_REGISTER
from .constants import ACTIVITY_RESET_PASSWORD
from .constants import ACTIVITY_SET_EMAIL
from .constants import ACTIVITY_SET_PASSWORD
from .managers import AddressActivityManager
from .managers import AddressManager
from .modelfields import LinkTarget
from .modelfields import LocalizedCharField
from .querysets import AddressActivityQuerySet
from .querysets import AddressQuerySet


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MenuItem(MPTTModel, BaseModel):
    title = LocalizedCharField(max_length=32, help_text=_('Page title'))
    parent = TreeForeignKey('self', models.PROTECT, null=True, blank=True, related_name='children',
                            db_index=True)
    target = LinkTarget()
    _cached_data = None

    def __str__(self):
        return self.title.current

    class MPTTMeta:
        order_insertion_by = ['title_en']

    @property
    def navkey(self):
        """The key identifying this menuitem, used to display a menuitem as active."""

        return self.cached_data.get('navkey')

    @property
    def href(self):
        """Link to this menuitem in the current language."""

        lang = get_language()
        return self.cached_data.get(lang, {}).get('href', '')

    def is_active_parent(self, menuitem):
        return menuitem in self.cached_data['children']

    @property
    def cached_data(self):
        """Precomputed data in all languages."""

        lang = get_language()
        if lang is None:
            return {}

        if self._cached_data is None:
            data = {
                'navkey': self.target.menu_key,
                'children': [n.navkey for n in self.get_descendants()],
            }

            # set language-specific link
            for code, _name in settings.LANGUAGES:
                with translation.override(code):
                    data[code] = {
                        'href': self.target.href,
                    }

            self._cached_data = data

        return self._cached_data


class CachedMessage(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_index=True)
    level = models.IntegerField()
    message = models.TextField()
    payload = JSONField(default=dict)


class Address(models.Model):
    objects = AddressManager.from_queryset(AddressQuerySet)()

    address = models.GenericIPAddressField()
    activities = models.ManyToManyField(settings.AUTH_USER_MODEL, through='AddressActivity')

    class Meta:
        verbose_name = _('IP-Address')
        verbose_name_plural = _('IP-Addresses')

    def __str__(self):
        return self.address


class AddressActivity(models.Model):
    objects = AddressActivityManager.from_queryset(AddressActivityQuerySet)()

    address = models.ForeignKey(Address, models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)

    ACTIVITY_CHOICES = {
        ACTIVITY_FAILED_LOGIN: _('Failed login'),
        ACTIVITY_REGISTER: _('Registration'),
        ACTIVITY_RESET_PASSWORD: _('Reset password'),
        ACTIVITY_SET_EMAIL: _('Set email'),
        ACTIVITY_SET_PASSWORD: _('Set password'),
    }

    timestamp = models.DateTimeField(auto_now_add=True)
    activity = models.SmallIntegerField(
        choices=sorted([(k, v) for k, v in ACTIVITY_CHOICES.items()], key=lambda t: t[0]))
    note = models.CharField(max_length=255, default='', blank=True)
    headers = JSONField(help_text=_('Request headers used.'))

    class Meta:
        verbose_name = _('IP-Address Activity')
        verbose_name_plural = _('IP-Address Activities')

    def __str__(self):
        return '%s: %s/%s' % (self.ACTIVITY_CHOICES[self.activity],
                              self.address.address, self.user.username)
