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

import re

import bleach

from lxml import html

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.safestring import mark_safe
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
from .modelfields import LocalizedTextField
from .querysets import AddressActivityQuerySet
from .querysets import AddressQuerySet
from .utils import canonical_link


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BasePage(BaseModel):
    title = LocalizedCharField(max_length=255, help_text=_('Page title'))
    slug = LocalizedCharField(max_length=255, unique=True, help_text=_('Slug (used in URLs)'))
    text = LocalizedTextField()
    published = models.BooleanField(default=True, help_text=_(
        'Wether or not the page is public.'))

    meta_summary = LocalizedCharField(
        max_length=160, blank=True, verbose_name=_('Meta'), help_text=_(
            'For search engines, max. of 160 characters.'))
    twitter_summary = LocalizedCharField(
        max_length=200, blank=True, verbose_name=_('Twitter'),
        help_text=_('At most 200 characters.'))
    opengraph_summary = LocalizedCharField(
        max_length=255, blank=True, verbose_name=_('Facebook'), help_text=_(
            'Two to four sentences, default: first three sentences.'))
    html_summary = LocalizedTextField(blank=True, verbose_name="HTML", help_text=_(
        'Any length, but must be valid HTML. Shown in RSS feeds.'))

    def render(self, context, summary=False):
        if summary is True:
            return mark_safe(self.get_html_summary(context['request']))
        else:
            t = '{%% load blog core bootstrap %%}%s' % self.text.current
            return template.Template(t).render(context)

    def render_from_request(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        context = template.RequestContext(request, extra_context)

        return self.render(context)

    def get_text_summary(self):
        text = html.fromstring(self.text.current).text_content()
        return re.sub('[\r\n]+', '\n', text).split('\n', 1)[0].strip(' \n').strip()

    def get_sentences(self, summary):
        """Split a text into sentences.

        At the most basic level, this function splits the given text on occurence of a dot (".")
        and one or more spaces. A semicolon is recognized as a sentence, so "foo: bar." counts as
        two sentences and the semicolon will not be preserved. A dot does not count as a sentence
        if it is preceeded by a number ("16. February") and only if followed by a space, a "<" (for
        HTML tags) or as end of string.
        """
        return ['%s.' % m.strip(' .:') for m in re.split('(?<![.0-9])[:.](?=[ <\Z])', summary)]

    def crop_summary(self, summary, length):
        sentences = self.get_sentences(summary)
        summary = ''
        for sentence in sentences:
            new_summary = '%s %s.' % (summary, sentence)
            if len(new_summary) > length:
                # If summary is currently Falsy, we return new_summary instead. This happens when
                # the first sentence is already longer then 160 chars.
                return summary or new_summary
            summary = new_summary
        return summary.strip()

    def get_meta_summary(self):
        if self.meta_summary.current:
            return self.meta_summary.current

        full_summary = self.get_text_summary()
        if len(full_summary) <= 160:
            return full_summary
        return self.crop_summary(full_summary, 160).strip()

    def get_twitter_summary(self):
        if self.twitter_summary.current:
            return self.twitter_summary.current
        if self.meta_summary.current:
            return self.meta_summary.current

        full_summary = self.get_text_summary()
        if len(full_summary) <= 200:
            return full_summary
        return self.crop_summary(full_summary, 200).strip()

    def get_opengraph_summary(self):
        if self.opengraph_summary.current:
            return self.opengraph_summary.current.strip()
        twitter_summary = self.get_twitter_summary()
        if twitter_summary:
            return twitter_summary

        summary = self.get_text_summary()
        return ' '.join(self.get_sentences(summary)[:3]).strip()

    def cleanup_html(self, html):
        tags = ['a', 'p', 'strong']
        attrs = {
            'a': ['href', ],
        }
        return bleach.clean(html, tags=tags, attributes=attrs, strip=True)

    def get_html_summary(self, request):
        if self.html_summary.current:
            return self.cleanup_html(self.html_summary.current)

        summary = self.render_from_request(request)

        html = ' '.join(self.get_sentences(summary)[:3]).strip()
        return self.cleanup_html(html)

    def get_canonical_url(self):
        """Get the full canonical URL of this object."""
        return canonical_link(self.get_absolute_url())

    class Meta:
        abstract = True


class Page(BasePage):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True,
                               related_name='old_author_page')

    def get_absolute_url(self):
        return reverse('blog:page', kwargs={'slug': self.slug.current})

    def __str__(self):
        return self.title.current


class BlogPost(BasePage):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, models.SET_NULL, null=True, blank=True,
                               related_name='old_author_post')

    sticky = models.BooleanField(default=False, help_text=_(
        'Pinned at the top of any list of blog posts.'))

    def get_absolute_url(self):
        return reverse('blog:blogpost', kwargs={'slug': self.slug.current})

    def __str__(self):
        return self.title.current


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
