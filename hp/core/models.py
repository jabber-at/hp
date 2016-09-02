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
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

#from composite_field.l10n import LocalizedCharField
#from composite_field.l10n import LocalizedTextField
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

from .constants import ACTIVITY_REGISTER
from .constants import ACTIVITY_RESET_PASSWORD
from .constants import ACTIVITY_SET_EMAIL
from .constants import ACTIVITY_SET_PASSWORD
from .managers import AddressActivityManager
from .modelfields import LinkTarget
from .modelfields import LocalizedCharField
from .modelfields import LocalizedTextField
from .querysets import AddressActivityQuerySet


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BasePage(BaseModel):
    title = LocalizedCharField(max_length=64, help_text=_('Page title'))
    slug = LocalizedCharField(max_length=64, unique=True, help_text=_('Slug (used in URLs)'))
    text = LocalizedTextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL)
    published = models.BooleanField(default=True, help_text=_(
        'Wether or not the page is public.'))

    class Meta:
        abstract = True


class Page(BasePage):
    def get_absolute_url(self):
        return reverse('core:page', kwargs={'slug': self.slug.current})

    def __str__(self):
        return self.title.current

class BlogPost(BasePage):
    sticky = models.BooleanField(default=False, help_text=_(
        'Pinned at the top of any list of blog posts.'))

    def get_absolute_url(self):
        return reverse('core:blogpost', kwargs={'slug': self.slug.current})

    def __str__(self):
        return self.title.current


class MenuItem(MPTTModel, BaseModel):
    title = LocalizedCharField(max_length=16, help_text=_('Page title'))
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


class Address(models.Model):
    address = models.GenericIPAddressField()
    activities = models.ManyToManyField(settings.AUTH_USER_MODEL, through='AddressActivity')

    class Meta:
        verbose_name = _('IP-Address')
        verbose_name_plural = _('IP-Addresses')

    def __str__(self):
        return self.address


class AddressActivity(models.Model):
    objects = AddressActivityManager.from_queryset(AddressActivityQuerySet)

    address = models.ForeignKey(Address)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    ACTIVITY_CHOICES = {
        ACTIVITY_REGISTER: _('Registration'),
        ACTIVITY_RESET_PASSWORD: _('Reset password'),
        ACTIVITY_SET_PASSWORD: _('Set password'),
        ACTIVITY_SET_EMAIL: _('Set email'),
    }

    timestamp = models.DateTimeField(auto_now_add=True)
    activity = models.SmallIntegerField(
        choices=sorted([(k, v) for k, v in ACTIVITY_CHOICES.items()], key=lambda t: t[0]))
    note = models.CharField(max_length=255, default='', blank=True)

    class Meta:
        verbose_name = _('IP-Address Activity')
        verbose_name_plural = _('IP-Address Activities')

    def __str__(self):
        return '%s: %s/%s' % (self.ACTIVITY_CHOICES[self.activity],
                              self.address.address, self.user.username)
