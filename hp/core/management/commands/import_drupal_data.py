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

import json
import re

from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...constants import TARGET_MODEL
from ...constants import TARGET_NAMED_URL
from ...constants import TARGET_URL
from ...modelfields import LinkTargetDict
from ...models import BlogPost
from ...models import MenuItem
from ...models import Page

User = get_user_model()


class Command(BaseCommand):
    """

    Create drupal dump with::

        drush --uri=https://jabber.at node-export --type=story,page --format=json --file=export.txt
    """
    help = "Import a Drupal data export."
    _link_cache = None

    def add_arguments(self, parser):
        parser.add_argument('input', help="Path to input file.")

    def handle_data(self, page, data, item=None):
        lang = data['language']
        setattr(page, 'title_%s' % lang, data['title'])
        setattr(page, 'text_%s' % lang, data['body']['und'][0]['value'])
        if data['path']:
            slug = data['path']['alias']
        else:
            slug = data['title']

        slug = re.sub('[^a-z0-9-_üöäß]', '-', slug.lower()).strip('-')
        slug = re.sub('-+', '-', slug)
        setattr(page, 'slug_%s' % lang, slug)

        if item and data.get('menu'):
            setattr(item, 'title_%s' % lang, data['menu']['link_title'])

    def parse_timestamp(self, stamp):
        return timezone.make_aware(datetime.fromtimestamp(int(stamp)))

    def handle_match(self, text, match):
        href = re.search('href=(?P<quotechar>["\'])(.*?)(?P=quotechar)', match)
        if not href:
            return text

        href = href.groups()[1]
        if re.match('https?://', href):
            return text

        linktext = re.search('>(.*?)</a>', match).groups()[0]
        if self._link_cache is None:
            self._link_cache = {
                '/de/apt-repositories': Page.objects.get(slug_de='apt-repository'),
                '/de/features': Page.objects.get(slug_de='apt-repository'),
                '/de/features/apt': Page.objects.get(slug_de='apt-repository'),
                '/de/features/firewalls': Page.objects.get(slug_de='features-firewalls'),
                '/de/features/webpresence': Page.objects.get(slug_de='features-webpresence'),
                '/de/privacy': Page.objects.get(slug_de='privatsphäre'),
                '/de/privatsphäre': Page.objects.get(slug_de='privatsphäre'),
                '/en/apt-repositories': Page.objects.get(slug_en='apt-repository'),
                '/en/apt-repository': Page.objects.get(slug_en='apt-repository'),
                '/en/features': Page.objects.get(slug_en='features'),
                '/en/features/apt': Page.objects.get(slug_en='apt-repository'),
                '/en/features/apt-repository': Page.objects.get(slug_en='apt-repository'),
                '/en/features/firewalls': Page.objects.get(slug_en='features-firewalls'),
                '/en/features/webpresence': Page.objects.get(slug_en='webpresence'),
                '/en/how-good-tls-encryption': BlogPost.objects.get(
                    slug_en='how-good-tls-encryption'),
                '/en/privacy-policy': Page.objects.get(slug_en='privacy'),
                '/en/privacy': Page.objects.get(slug_en='privacy'),
                '/en/webpresence': Page.objects.get(slug_en='features-firewalls'),
                '/de/privatsphäre#legal': Page.objects.get(slug_de='privatsphäre'),
                '/en/privacy-policy#legal': Page.objects.get(slug_en='privacy'),

                '/en/contact': {'path': 'core:contact'},
                '/de/contact': {'path': 'core:contact'},
                '/contact': {'path': 'core:contact'},
                '/de/register': {'path': 'account:register'},
                '/en/register': {'path': 'account:register'},
                '/stats': {'url': 'https://stats.jabber.at'},
                '/logs': {'url': '/logs'},
                '/': {'path': 'blog:home'},
                '/presence/themes': {'url': 'https://http.jabber.at/presence/themes'},

                '/de/node/25': Page.objects.get(slug_de='apt-repository'),
                '/en/node/132': BlogPost.objects.get(slug_en='change-in-password-reset-policy'),
                '/en/node/130': BlogPost.objects.get(slug_en='downtime-saturday-may-2-9-00-cest'),
            }

        target = self._link_cache.get(href)

        if target is None:
            return text

        if isinstance(target, Page):
            anchor = ''
            if '#' in href:
                _, anchor = href.split('#', 1)
                anchor = 'anchor="%s" ' % anchor

            replacement = '{%% page %s title="%s" %s%%}' % (target.pk, linktext, anchor)
        elif isinstance(target, BlogPost):
            replacement = '{%% post %s title="%s" %%}' % (target.pk, linktext)
        elif isinstance(target, dict):
            if target.get('path'):
                replacement = '{%% path "%s" "%s" %%}' % (target['path'], linktext)
            elif target.get('url'):
                replacement = match.replace(href, target.get('url'))
            else:
                raise ValueError("Unknown target type %s" % type(target))
        else:
            raise ValueError("Unknown target type %s" % type(target))

        return text.replace(match, replacement)

    def handle(self, input, **kwargs):
        with open(input) as stream:
            docs = json.load(stream)

        # Delete all pages for now
        Page.objects.all().delete()
        BlogPost.objects.all().delete()
        MenuItem.objects.all().delete()

        page_ctype = ContentType.objects.get_for_model(Page)

        self.stdout.write('Loaded %s documents.' % len(docs))
        pages = {d['nid']: d for d in docs if d['type'] == 'page'}
        stories = {d['nid']: d for d in docs if d['type'] == 'story'}
        self.stdout.write('... found %s pages.' % len(pages))
        self.stdout.write('... found %s stories.' % len(stories))

        for nid, page_data in pages.items():
            if nid != page_data['tnid']:  # translated page
                continue

            self.stdout.write('Create %s' % page_data['title'])
            page = Page()

            # so we can set the fields, otherwise the ORM sets this automatically
            page._meta.get_field('updated').auto_now = False
            page._meta.get_field('created').auto_now_add = False

            page.created = self.parse_timestamp(page_data['created'])
            page.updated = self.parse_timestamp(page_data['changed'])
            page.published = bool(int(page_data['status']))

            item = MenuItem()

            self.handle_data(page, page_data, item)
            for translated_data in [p for p in pages.values() if p['tnid'] == nid]:
                self.handle_data(page, translated_data, item)

            nodename = page_data['name'].lower()
            if not nodename:  # one page (links) has no author name for some reason
                nodename = 'mati'

            username = '%s@jabber.at' % nodename
            page.author = User.objects.get_or_create(username=username)[0]
            page.save()

            if page_data.get('menu'):
                item.target = LinkTargetDict(
                    typ=TARGET_MODEL,
                    content_type=page_ctype.pk,
                    object_id=page.pk,
                )
                item.save()

        # We manually set some menu items

        features_item = MenuItem(title_de='de', title_en='en')
        features_item.target = LinkTargetDict(typ=TARGET_URL, url='#')
        features_item.save()

        for title in ['Webpresence', 'Security', 'Firewall connectivity', 'APT repository',
                      'Features', ]:
            child_item = MenuItem.objects.get(title_en=title)
            child_item.move_to(features_item)

        overview_item = MenuItem.objects.get(title_en='Features')
        overview_item.title_en = 'Overview'
        overview_item.title_de = 'Übersicht'
        overview_item.save()

        features_item.title_de = 'Features'
        features_item.title_en = 'Features'
        features_item.save()

        # add a contact menu item
        MenuItem.objects.create(title_de="Kontakt", title_en="Contact", target=LinkTargetDict(
            typ=TARGET_NAMED_URL, name='core:contact', args=(), kwargs={},
        ))
        MenuItem.objects.rebuild()

        for nid, post_data in stories.items():
            if nid != post_data['tnid']:  # translated post
                continue

            self.stdout.write('Create %s' % post_data['title'])
            post = BlogPost()

            # so we can set the fields, otherwise the ORM sets this automatically
            post._meta.get_field('updated').auto_now = False
            post._meta.get_field('created').auto_now_add = False

            post.created = self.parse_timestamp(post_data['created'])
            post.updated = self.parse_timestamp(post_data['changed'])
            post.published = bool(int(post_data['status']))
            post.sticky = bool(int(post_data['sticky']))

            self.handle_data(post, post_data)
            for translated_data in [p for p in stories.values() if p['tnid'] == nid]:
                self.handle_data(post, translated_data)

            nodename = post_data['name'].lower()
            username = '%s@jabber.at' % nodename
            post.author = User.objects.get_or_create(username=username)[0]
            post.save()

        for page in Page.objects.all():
            for match in re.finditer('(<[aA] .*?</a>)', page.text_de):
                page.text_de = self.handle_match(page.text_de, match.groups()[0])
            for match in re.finditer('(<[aA] .*?</a>)', page.text_en):
                page.text_en = self.handle_match(page.text_en, match.groups()[0])
            page.save()

        for post in BlogPost.objects.all():
            for match in re.finditer('(<[aA] .*?</a>)', post.text_de):
                post.text_de = self.handle_match(post.text_de, match.groups()[0])
            for match in re.finditer('(<[aA] .*?</a>)', post.text_en):
                post.text_en = self.handle_match(post.text_en, match.groups()[0])
            post.save()
