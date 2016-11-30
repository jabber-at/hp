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
from django.utils.translation import ugettext_lazy as _

from blog.sitemaps import BlogPostSitemap
from blog.sitemaps import PageSitemap

from . import views
from .sitemaps import StaticSitemap

sitemaps = {
    'blog': BlogPostSitemap,
    'page': PageSitemap,
    'static': StaticSitemap,
}


app_name = 'core'
urlpatterns = [
    url(_(r'^contact/$'), views.ContactView.as_view(), name='contact'),
    url(_(r'^clients/$'), views.ClientsView.as_view(), name='clients'),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap'),
    url(r'^api/set-lang/$', views.SetLanguageView.as_view(), name='api-set-lang'),
]
