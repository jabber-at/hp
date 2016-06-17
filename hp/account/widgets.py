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

from django import forms
from django.conf import settings

from bootstrap.widgets import BootstrapWidgetMixin


class UsernameWidget(BootstrapWidgetMixin, forms.MultiWidget):
    def decompress(self, value):
        if value:
            return value.split('@', 1)
        return '', settings.DEFAULT_XMPP_HOST

    class Media:
        js = (
            'xmpp_accounts/js/jid_widget.js',
        )
