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

from composite_field.l10n import LocalizedCharField
from composite_field.l10n import LocalizedTextField
from django_confirm.models import Confirmation as BaseConfirmation
from mptt.models import MPTTModel
from mptt.models import TreeForeignKey

from .modelfields import LinkTarget


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


class Confirmation(BaseConfirmation):
    class Meta:
        proxy = True

    def send(self, request, user, purpose, subject, **kwargs):
        node, domain = user.get_username().split('@', 1)

        label = self._meta.app_label

        path = reverse('%s:%s_confirm' % (label, purpose), kwargs={'key': self.key, })
        uri = request.build_absolute_uri(location=path)

        kwargs.setdefault('subject', subject)
        #kwargs.setdefault('sender', request.site.get('FROM_EMAIL', settings.DEFAULT_FROM_EMAIL))
        kwargs.setdefault('sender', settings.DEFAULT_FROM_EMAIL)
        kwargs.setdefault('txt_template', '%s/confirm/%s.txt' % (label, purpose))
        kwargs.setdefault('html_template', '%s/confirm/%s.html' % (label, purpose))
        kwargs.setdefault('lang', request.LANGUAGE_CODE)
        kwargs.setdefault('gpg_opts', getattr(settings, 'GNUPG', None))

        kwargs.setdefault('extra_context', {})
        kwargs['extra_context'].update({
            'username': node,
            'domain': domain,
            'jid': user.get_username(),
            'uri': uri,
        })
        return super(Confirmation, self).send(**kwargs)
