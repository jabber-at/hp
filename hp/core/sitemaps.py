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

from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class SitemapMixin(object):
    protocol = 'https'
    i18n = True

    def changefreq(self, item):
        return 'daily'

    def get_urls(self, **kwargs):
        """Overwritten to remove duplicate URLs.

        In some cases, URLs are identical for different languages.
        """
        done = set()
        for url in super(SitemapMixin, self).get_urls(**kwargs):
            if url['location'] in done:
                continue

            done.add(url['location'])
            yield url


class StaticSitemap(SitemapMixin, Sitemap):
    def items(self):
        return [
            'core:contact', 'account:register', 'account:login', 'account:reset_password',
        ]

    def location(self, item):
        return reverse(item)
