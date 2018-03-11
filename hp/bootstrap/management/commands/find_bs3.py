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
    'table-condensed': 'Rename table.table-condensed to table.table-sm.',
    'table-row-context-class': 'Contextual classes (active, success, info, warning, danger) on table rows '
                               'use a "table-" prefix. So change tr.active to tr.table-active and so on.',
    'table-cell-context-class': 'Contextual classes (active, success, info, warning, danger) on table cells '
                                'use a "table-" prefix. So change td.active to td.table-active and so on.',

    'img-responsive': 'Rename .img-responsive to .img-fluid.',
    'img-rounded': 'Rename .img-rounded to .rounded.',
    'img-circle': 'Rename .img-circle to .rounded-circle.',
    'page-header': '.page-headeris no longer supported, aside from the border, all its styles can be applied '
                   'via utilities.',
    'btn-default': 'Rename .btn-default to .btn-secondary.',
    'old-labels':
        'Labels have been renamed to badges, see http://getbootstrap.com/docs/4.0/components/badge/.',
    'glyphicon': 'Found an old Glyphicon, which are no longer supported by Bootstrap4. '
                 'Use fontawesome icons instead, which are now integrated into the editor. Old Glyphicons '
                 'will show up as "DEPRECATED GLYPHICON" in the editor.'
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

            if html.cssselect('.table-condensed'):
                self.log_tag(obj, 'table-condensed', lang)
            if html.cssselect('tr.active, tr.success, tr.info, tr.warning, tr.danger'):
                self.log_tag(obj, 'table-row-context-class', lang)
            if html.cssselect('td.active, td.success, td.info, td.warning, td.danger'):
                self.log_tag(obj, 'table-cell-context-class', lang)
            if html.cssselect('th.active, th.success, th.info, th.warning, th.danger'):
                self.log_tag(obj, 'table-cell-context-class', lang)

            if html.cssselect('.img-responsive'):
                self.log_tag(obj, 'img-responsive', lang)
            if html.cssselect('.img-rounded'):
                self.log_tag(obj, 'img-rounded', lang)
            if html.cssselect('.img-circle'):
                self.log_tag(obj, 'img-circle', lang)
            if html.cssselect('.page-header'):
                self.log_tag(obj, 'page-header', lang)
            if html.cssselect('.btn-default'):
                self.log_tag(obj, 'btn-default', lang)
            if html.cssselect('span.label'):
                self.log_tag(obj, 'old-labels', lang)
            if html.cssselect('.glyphicon'):
                self.log_tag(obj, 'glyphicon', lang)

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
