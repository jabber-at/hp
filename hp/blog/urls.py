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

from django.conf.urls import url
from django.contrib.sitemaps.views import sitemap

from . import views
from .sitemaps import BlogPostSitemap
from .sitemaps import PageSitemap

sitemaps = {
    'blog': BlogPostSitemap,
    'page': PageSitemap,
}


app_name = 'core'
urlpatterns = [
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps, },
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'^api/set-lang/$', views.SetLanguageView.as_view(), name='api-set-lang'),
    url(r'^$', views.BlogPostListView.as_view(), name='home'),
]
