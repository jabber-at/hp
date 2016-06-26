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

        # replace some links so they work out of the box
        text = getattr(page, 'text_%s' % lang)
        for old, new in [
            ('/de/empfohlene-clients/?', '/clients/'),
            ('/de/features/?', '/features/'),
            ('/de/features/apt/?', '/apt-repository/'),
            ('/de/features/firewalls/?', '/features-firewalls/'),
            ('/de/features/webpresence/?', '/features-webpresence/'),
            ('/en/features/?', '/features/'),
            ('/en/features/apt/?', '/apt-repository/'),
            ('/en/features/firewalls/?', '/features-firewalls/'),
            ('/en/features/webpresence/?', '/features-webpresence/'),
            ('/en/webpresence/?', '/features-webpresence/'),
            ('/en/privacy-policy/?', '/privacy/'),
            ('account.jabber.at/password/?', '/account/password/reset/'),
            ('https://account.jabber.at/password/', '/account/password/reset/'),
            ('https://webchat.jabber.at/?', '/chat/'),
        ]:
            text = re.sub(r'href=[\'"]%s[\'"]' % old, 'href="%s"' % new, text)
        setattr(page, 'text_%s' % lang, text)

        slug = re.sub('[^a-z0-9-_üöäß]', '-', slug.lower()).strip('-')
        slug = re.sub('-+', '-', slug)
        setattr(page, 'slug_%s' % lang, slug)

        if item and data.get('menu'):
            setattr(item, 'title_%s' % lang, data['menu']['link_title'])

    def parse_timestamp(self, stamp):
        return timezone.make_aware(datetime.fromtimestamp(int(stamp)))

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

            page.author = User.objects.get_or_create(username='%s@jabber.at' % page_data['name'])[0]
            page.save()

            if page_data.get('menu'):
                item.target = LinkTargetDict(
                    typ=TARGET_MODEL,
                    content_type=page_ctype.pk,
                    object_id=page.pk,
                )
                item.save()

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

            post.author = User.objects.get_or_create(username='%s@jabber.at' % post_data['name'])[0]
            post.save()
