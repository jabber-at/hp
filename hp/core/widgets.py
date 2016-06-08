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

import json

from django import forms

from .constants import TARGET_URL
from .constants import TARGET_PAGE


class LinkTargetWidget(forms.MultiWidget):
    def decompress(self, value):
        if value is None:
            return [TARGET_URL, '', 1]
        value = json.loads(value)
        typ = value.get('typ', TARGET_URL)

        if typ == TARGET_URL:
            return [typ, value.get('url', ''), 1]
        elif typ == TARGET_PAGE:
            return [typ, '', value.get('page', 1)]
        return [TARGET_URL, '', 1]
