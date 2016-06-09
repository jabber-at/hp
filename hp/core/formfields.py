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

import logging

from django import forms

from .constants import TARGET_CHOICES
from .constants import TARGET_PAGE
from .constants import TARGET_URL
from .models import Page
from .widgets import LinkTargetWidget

log = logging.getLogger(__name__)


class LinkTargetField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (
            forms.ChoiceField(choices=TARGET_CHOICES.items()),  # type
            forms.CharField(required=False),  # any absolute URL
            forms.ModelChoiceField(queryset=Page.objects.filter(published=True), required=False),

        )
        self.widget = LinkTargetWidget(widgets=[f.widget for f in fields])

        super(LinkTargetField, self).__init__(fields=fields,
                                              require_all_fields=False, *args,
                                              **kwargs)

    def compress(self, data_list):
        print('### compress(%s)' % (data_list, ))
        typ = int(data_list.pop(0))
        if typ == TARGET_URL:
            return {
                'typ': typ,
                'url': data_list.pop(0),
            }
        elif typ == TARGET_PAGE:
            return {
                'typ': typ,
                'page': data_list.pop(1).pk,
            }
        log.warn('Unknown link target type: %s', typ)
        return {}
