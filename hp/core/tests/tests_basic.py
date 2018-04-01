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

import doctest

from django.test import Client
from django.test import override_settings

from .. import utils
from ..templatetags import icons
from .base import TestCase


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(utils))
    tests.addTests(doctest.DocTestSuite(icons))
    return tests


@override_settings(MIDDLEWARE=[
    'django.contrib.sessions.middleware.SessionMiddleware',  # required by AuthenticationMiddleware
    'django.middleware.locale.LocaleMiddleware',  # required by standard view
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # required by HomepageMiddleware
    'core.middleware.HomepageMiddleware',
])
class MiddlewareTestCase(TestCase):
    def test_basic(self):
        c = Client()
        with self.assertTemplateUsed('blog/blogpost_list.html'):
            response = c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.wsgi_request.os, 'any')
            self.assertTrue(response.wsgi_request.os_mobile)
            # If we execute the test-suite with "manage.py test" instead of "fab test", localsettings will be
            # used and the results are different.
            self.assertEqual(response.wsgi_request.site['NAME'], 'example.com', 'Tested with fab test?')
