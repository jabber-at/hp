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
# You should have received a copy of the GNU General Public License along with this project. If
# not, see <http://www.gnu.org/licenses/>.

from lxml import etree

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import translation
from django.utils.http import http_date
from django.utils.translation import ugettext as _
from django.views.generic.base import View
from django.views.generic.list import MultipleObjectMixin

from core.models import BlogPost


class FeedMixin(MultipleObjectMixin):
    queryset = BlogPost.objects.published().blog_order()
    content_type = 'application/xml'

    def sub(self, root, tag, text=None, **attrs):
        e = etree.SubElement(root, tag, **attrs)
        if text:
            e.text = text
        return e

    def get_content_type(self):
        return self.content_type

    def get(self, request, language):
        ctype = self.get_content_type()

        with translation.override(language):
            items = self.serialize_items(request, language, self.get_queryset()[:15])
            return HttpResponse(etree.tostring(items), ctype, charset='utf-8')


class AtomFeed(FeedMixin, View):
        pass


class RSS2Feed(FeedMixin, View):
    """Generate a RSS 2.0 feed.

    .. seealso::

       * `Specification <http://www.rssboard.org/rss-specification>`_
       * `Validator <http://www.rssboard.org/rss-validator>`_
    """
    def serialize_items(self, request, language, queryset):
        root = etree.Element("rss", version="2.0")
        channel = self.sub(root, 'channel')

        self.sub(channel, 'title', _('%s - Recent updates') % request.site['BRAND'])
        self.sub(channel, 'link', request.build_absolute_uri(reverse('core:home')))
        self.sub(channel, 'description', _('Follow recent updates for %s') % request.site['BRAND'])
        self.sub(channel, 'language', language)
        self.sub(channel, 'lastBuildDate', http_date())
        # TODO: image, skipHours

        for post in queryset:
            path = reverse('core:blogpost', kwargs={'slug': post.slug.current})

            item = self.sub(channel, 'item')
            self.sub(item, 'title', post.title.current)
            self.sub(item, 'description', post.text.current[:160])
            self.sub(item, 'link', request.build_absolute_uri(path))
            self.sub(item, 'author', post.author.node)
            self.sub(item, 'guid', 'https://jabber.at%s' % path, isPermaLink='true')
            self.sub(item, 'pubDate', http_date(post.created.timestamp()))

        return root
