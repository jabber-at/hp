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

import textwrap

from lxml.html import fromstring

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.urls import reverse

from blog.models import BlogPost
from blog.models import Page

TAGS = {
    'responsive-table-div': 'Responsive tables no longer require a wrapping element. Instead, just put the '
                            '.table-responsive right on the <table>.',
}


class Command(BaseCommand):
    help = 'Find old Bootstrap v3 markup'

    def add_arguments(self, parser):
        languages = [l[0] for l in settings.LANGUAGES]

        parser.add_argument('-l', '--lang', choices=languages, metavar='LANG', action='append', default=[],
                            help="Only scan the respective language.")
        parser.add_argument('-t', '--tag', help="Describe a given tag in more detail.")

        bp_group = parser.add_mutually_exclusive_group()
        bp_group.add_argument('-b', '--blog-posts', dest='only', action='store_const', const='posts',
                              help="Only scan blog posts.")
        bp_group.add_argument('-p', '--pages', dest='only', action='store_const', const='pages',
                              help="Only scan pages.")

    def log_tag(self, obj, tag, lang):
        url = reverse("admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name), args=(obj.id, ))
        self.stdout.write('%s (lang=%s): %s' % (url, lang, tag))

    def scan_base_page(self, obj, languages):
        for lang in languages:
            field = 'text_%s' % lang
            text = getattr(obj, field)

            html = fromstring(text)
            try:
                if html.cssselect('div.table-responsive table'):
                    self.log_tag(obj, 'responsive-table-div', lang)
            except ImportError as e:
                raise CommandError(str(e))

    def handle(self, *args, **options):
        if options['tag']:
            try:
                help_text = TAGS[options['tag']]
            except KeyError:
                raise CommandError('Unknown tag.')

            self.stdout.write('%s:' % options['tag'])
            self.stdout.write('')
            wrapped = textwrap.wrap(help_text, initial_indent='    ', subsequent_indent='    ', width=78)
            self.stdout.write('\n'.join(wrapped))

            return

        only = options['only']
        languages = options['lang'] or [l[0] for l in settings.LANGUAGES]

        if only == 'pages' or only is None:
            for page in Page.objects.all():
                self.scan_base_page(page, languages=languages)

        if only == 'posts' or only is None:
            for post in BlogPost.objects.all():
                self.scan_base_page(post, languages=languages)
