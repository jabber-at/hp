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
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import HttpResponse
from django.utils import timezone
from django.utils import translation
from django.utils.http import http_date
from django.utils.translation import ugettext as _
from django.views.generic.base import View
from django.views.generic.list import MultipleObjectMixin

from blog.models import BlogPost
from core.utils import absolutify_html


class FeedMixin(MultipleObjectMixin):
    queryset = BlogPost.objects.published().blog_order()
    content_type = 'application/xml'
    atom_ns = 'http://www.w3.org/2005/Atom'

    def sub(self, root, tag, text=None, **attrs):
        e = etree.SubElement(root, tag, **attrs)
        if text:
            e.text = text
        return e

    def get_content_type(self):
        return self.content_type

    def get_feed_title(self, request):
        return _('%s - Recent updates') % request.site['BRAND']

    def get(self, request, language):
        ctype = self.get_content_type()

        with translation.override(language):
            items = self.serialize_items(request, language, self.get_queryset()[:15])
            return HttpResponse(etree.tostring(items), ctype, charset='utf-8')


class AtomFeed(FeedMixin, View):
    """Generate an Atom feed.

    .. seealso::

        * `Introduction <https://validator.w3.org/feed/docs/atom.html>`_
        * `Specification <https://validator.w3.org/feed/docs/rfc4287.html>`_
        * `Validator <https://validator.w3.org/feed/docs/atom.html>`_
    """

    def serialize_items(self, request, language, queryset):
        default_host = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]
        base_url = default_host['CANONICAL_BASE_URL']
        feed_id = '%s%s' % (base_url, request.get_full_path())

        root = etree.Element("feed", nsmap={
            None: self.atom_ns,
            'dc': 'http://purl.org/dc/elements/1.1/',
        })
        self.sub(root, 'title', self.get_feed_title(request))
        self.sub(root, 'id', feed_id)

        try:
            updated = max([q.updated for q in queryset])
        except ValueError:
            updated = timezone.now()
        self.sub(root, 'updated', timestamp_to_rfc3339_utcoffset(int(updated.timestamp())))

        self.sub(root, 'link', href=feed_id, rel='self')
        self.sub(root, 'icon', static('feed/atom_icon.png'))
        self.sub(root, 'logo', static('feed/atom.png'))
        self.sub(root, 'rights', '© 2010-%s, jabber.at' % updated.year)

        for post in queryset:
            canonical_url = post.get_canonical_url()
            content = absolutify_html(post.render_from_request(request), base_url)
            summary = absolutify_html(post.get_html_summary(request), base_url)

            entry = self.sub(root, 'entry')
            self.sub(entry, 'id', canonical_url)
            self.sub(entry, 'title', post.title.current)
            self.sub(entry, 'updated', timestamp_to_rfc3339_utcoffset(
                int(post.updated.timestamp())))
            self.sub(entry, 'published', timestamp_to_rfc3339_utcoffset(
                int(post.created.timestamp())))
            self.sub(entry, 'link', href=canonical_url)
            self.sub(entry, 'content', content, type="html")
            self.sub(entry, 'summary', summary, type="html")

            author = self.sub(entry, 'author')
            self.sub(author, 'name', post.author.node)

        return root


class RSS2Feed(FeedMixin, View):
    """Generate a RSS 2.0 feed.

    .. seealso::

       * `Specification <http://www.rssboard.org/rss-specification>`_
       * `Validator <http://www.feedvalidator.org/>`_
    """
    def serialize_items(self, request, language, queryset):
        default_host = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]
        base_url = default_host['CANONICAL_BASE_URL']
        title = self.get_feed_title(request)
        feed_url = request.build_absolute_uri(reverse('blog:home'))

        # see: http://www.feedvalidator.org/docs/warning/MissingAtomSelfLink.html
        href = request.build_absolute_uri(request.get_full_path())

        root = etree.Element("rss", version="2.0", nsmap={
            'atom': self.atom_ns,
        })
        channel = self.sub(root, 'channel')

        self.sub(channel, 'title', title)
        self.sub(channel, 'link', feed_url)
        self.sub(channel, 'description', _('Follow recent updates for %s') % request.site['BRAND'])
        self.sub(channel, 'language', language)
        self.sub(channel, 'lastBuildDate', http_date())

        skipHours = self.sub(channel, 'skipHours')
        for i in range(0, 7):
            self.sub(skipHours, 'hour', text=str(i))

        # add image
        image = self.sub(channel, 'image')
        self.sub(image, 'title', title)
        self.sub(image, 'link', feed_url)
        self.sub(image, 'url', request.build_absolute_uri(static('feed/rss.png')))
        self.sub(image, 'width', '120')
        self.sub(image, 'height', '120')

        # add url (NOTE: This does not have anything to do with the Atom standard)
        self.sub(channel, '{%s}link' % self.atom_ns, rel='self', type='application/rss+xml',
                 href=href)

        for post in queryset:
            canonical_url = post.get_canonical_url()
            content = absolutify_html(post.get_html_summary(request), base_url)

            item = self.sub(channel, 'item')
            self.sub(item, 'title', post.title.current)
            self.sub(item, 'description', content)
            self.sub(item, 'link', canonical_url)
            self.sub(item, 'guid', canonical_url, isPermaLink='true')
            self.sub(item, 'pubDate', http_date(post.created.timestamp()))

            # We do not add an author element, because this *requires* an email address.
            #self.sub(item, 'author', post.author.node)

        return root
