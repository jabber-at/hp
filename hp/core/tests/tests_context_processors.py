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
from django.test import Client
from django.test import override_settings

from .base import TestCase


class ContextProcessorTestCase(TestCase):
    """Test core.context_processors.basic()."""

    def test_basic(self):
        c = Client()
        with self.assertTemplateUsed('blog/blogpost_list.html'):
            response = c.get('/')
            self.assertEqual(response.status_code, 200)

            self.assertEqual(response.context['os'], 'any')
            self.assertTrue(response.context['os_mobile'])
            self.assertEqual(response.context['site'], settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST])
            self.assertEqual(response.context['default_site'],
                             settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST])
            self.assertFalse(response.context['DEBUG'])
            self.assertEqual(response.context['LANGUAGE_CODE'], 'en')
            self.assertEqual(response.context['other_langs'], [('de', 'German')])

    def test_other_langs(self):
        c = Client()
        with override_settings(LANGUAGES=[
            ('de', 'German'),
            ('fr', 'French'),
        ], LANGUAGE_CODE='de'):
            response = c.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['LANGUAGE_CODE'], 'de')
            self.assertEqual(response.context['other_langs'], [('fr', 'French')])

    def assertOS(self, ua, os, mobile=True):
        c = Client()
        with self.assertTemplateUsed('blog/blogpost_list.html'):
            response = c.get('/', HTTP_USER_AGENT=ua)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['os'], os)
            self.assertEqual(response.context['os_mobile'], mobile)

    def test_os(self):
        self.assertOS('', 'any')
        self.assertOS('foo', 'any')
        self.assertOS('example', 'any')

        # Some popular ones from here:
        # https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
        self.assertOS('Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0', 'linux', False)
        self.assertOS(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',  # NOQA
            'win', False)
        self.assertOS(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',  # NOQA
            'win', False)
        self.assertOS('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0',
                      'win', False)
        self.assertOS(
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',  # NOQA
            'win', False)

        # ios from here:
        # https://developers.whatismybrowser.com/useragents/explore/operating_system_name/ios/
        self.assertOS(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',  # NOQA
            'ios', True)
        self.assertOS(
            'Mozilla/5.0 (iPad; CPU OS 10_2_1 like Mac OS X) AppleWebKit/602.4.6 (KHTML, like Gecko) Version/10.0 Mobile/14D27 Safari/602.1',  # NOQA
            'ios', True)
        self.assertOS(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_2_1 like Mac OS X) AppleWebKit/602.4.6 (KHTML, like Gecko) Version/10.0 Mobile/14D27 Safari/602.1',  # NOQA
            'ios', True)

        # a few osx:
        self.assertOS(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko)',
            'osx', False)
        self.assertOS(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7',  # NOQA
            'osx', False)
        self.assertOS(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/601.4.4 (KHTML, like Gecko) Version/9.0.3 Safari/601.4.4',  # NOQA
            'osx', False)
        self.assertOS(
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8',  # NOQA
            'osx', False)

        # Some Android:
        self.assertOS(
            'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko; googleweblight) Chrome/38.0.1025.166 Mobile Safari/535.19',  # NOQA
            'android', True)
        self.assertOS(
            'Dalvik/1.6.0 (Linux; U; Android 4.1.1; BroadSign Xpress 1.0.14 B- (720) Build/JRO03H)',
            'android', True)
        self.assertOS(
            'Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; BroadSign Xpress 1.0.15-6 B- (720) Build/JRO03H) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30',  # NOQA
            'android', True)
        self.assertOS(
            'Mozilla/5.0 (Linux; U; Android 4.0.4; pt-br; MZ608 Build/7.7.1-141-7-FLEM-UMTS-LA) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30',  # NOQA
            'android', True)
        self.assertOS(
            'Mozilla/5.0 (Linux; Android 6.0.1; SM-T800 Build/MMB29K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.107 Safari/537.36',  # NOQA
            'android', True)
        self.assertOS(
            'Mozilla/5.0 (Linux; Android; 4.1.2; GT-I9100 Build/000000) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1234.12 Mobile Safari/537.22 OPR/14.0.123.123',  # NOQA
            'android', True)
