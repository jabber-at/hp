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

from django.test import TestCase

from .models import Page


class BasePageTests(TestCase):
    # NOTE: You cannot instantiate a BasePage directly

    def test_cleanup_html(self):
        b = Page()
        self.assertEqual(b.cleanup_html('test'), 'test')
        self.assertEqual(b.cleanup_html('<a href="https://example.com">test'),
                         '<a href="https://example.com">test</a>')

        self.assertEqual(b.cleanup_html('test <table><tr><td>foo</td></tr></table>'),
                         'test foo')
