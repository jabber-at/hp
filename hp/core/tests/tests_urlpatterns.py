# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.test import Client
from django.test import override_settings
from django.utils.translation import gettext_lazy as _

from .. import views
from ..urlpatterns import i18n_re_path
from .base import TestCase

app_name = 'core'
urlpatterns = [
    i18n_re_path(_(r'^contact/$'), views.ContactView.as_view(), name='contact'),

    # URLs provided by these modules are used in the base template, so we have to include them here too
    url(r'^captcha/', include('captcha.urls')),
    url(r'^account/', include('account.urls')),
    url(r'^feed/', include('feed.urls')),
    url(r'^', include('blog.urls')),
    url(r'^', include('core.urls')),
]


@override_settings(ROOT_URLCONF=__name__)
class I18nURLTests(TestCase):
    def test_re_path(self):
        c = Client()
        with self.assertTemplateUsed('core/contact.html'):
            response = c.get('/contact/')
            self.assertEqual(response.status_code, 200)

        response = c.get('/kontakt/')
        self.assertRedirects(response, '/contact/')

        # Set language to German and test new redirects
        c.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'de'})
        with self.assertTemplateUsed('core/contact.html'):
            response = c.get('/kontakt/')
            self.assertEqual(response.status_code, 200)

        response = c.get('/contact/')
        self.assertRedirects(response, '/kontakt/')

        # Set language to French - translated URLs redirect to English version
        c.cookies.load({settings.LANGUAGE_COOKIE_NAME: 'fr'})
        response = c.get('/kontakt/')
        self.assertRedirects(response, '/contact/')

        with self.assertTemplateUsed('core/contact.html'):
            response = c.get('/contact/')
            self.assertEqual(response.status_code, 200)
