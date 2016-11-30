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

from core.sitemaps import SitemapMixin

from .models import BlogPost
from .models import Page


class BasePageSitemap(Sitemap):
    def lastmod(self, item):
        return item.updated


class BlogPostSitemap(SitemapMixin, BasePageSitemap):
    def items(self):
        return BlogPost.objects.filter(published=True)


class PageSitemap(SitemapMixin, BasePageSitemap):
    def items(self):
        return Page.objects.filter(published=True)
