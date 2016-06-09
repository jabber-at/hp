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
import logging

from django import forms

from .constants import TARGET_URL
from .constants import TARGET_NAMED_URL
from .constants import TARGET_MODEL

log = logging.getLogger(__name__)


class LinkTargetWidget(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        self.models = kwargs.pop('models', [])
        super(LinkTargetWidget, self).__init__(*args, **kwargs)

    def decompress(self, value):
        default_model = 1
        if self.models:
            default_model = self.models[0].pk

        if value is None:
            return [TARGET_URL, '', '', '', default_model, '']

        value = json.loads(value)
        typ = value.get('typ', TARGET_URL)

        if typ == TARGET_URL:
            return [typ, value.get('url', ''), '', '', default_model, '']
        elif typ == TARGET_NAMED_URL:
            return [typ, value.get('name', ''), value.get('args', '[]'), value.get('kwargs', '{}'),
                    default_model, '']
        elif typ == TARGET_MODEL:
            return [typ, '', '', '', value.get('content_type', 1), value.get('object_id')]
        log.error('Unkown typ %s', typ)
        return [TARGET_URL, '', '', '', default_model, '']
