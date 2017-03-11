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
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    target = LinkTarget()

    def __str__(self):
        return self.title.current

    class MPTTMeta:
        order_insertion_by = ['title_en']


class CachedMessage(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)
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

    address = models.ForeignKey(Address)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

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
