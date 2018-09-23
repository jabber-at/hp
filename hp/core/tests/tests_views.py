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

from django.urls import reverse

from .base import SeleniumTestCase


class SetLangTestCase(SeleniumTestCase):
    def test_basic(self):
        self.selenium.get('%s%s' % (self.live_server_url, reverse('blog:home')))
        self.wait_for_page_load()

        de_selector = '.lang-item-de a'
        en_selector = '.lang-item-en a'

        de_link = self.find(de_selector)
        self.assertDisplayed(de_link)
        self.assertNoElementExists(en_selector)

        de_link.click()
        self.wait_for_page_load()
        en_link = self.find(en_selector)
        self.assertDisplayed(en_link)
        self.assertNoElementExists(de_selector)
