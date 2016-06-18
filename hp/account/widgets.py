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
from django.utils.html import format_html

from bootstrap.widgets import BootstrapWidgetMixin
from bootstrap.widgets import BootstrapTextInput


class NodeWidget(forms.TextInput):
    """The widget used for rendering the node part (before the "@") of a username.

    This class is used because we want to render this widget in a bootstrap column.
    """

    def render(self, *args, **kwargs):
        html = super(NodeWidget, self).render(*args, **kwargs)
        return format_html('<div class="col-sm-8">{}</div>', html)


class DomainWidget(forms.Select):
    """The widget used for rendering the domain part of a username."""

    def render(self, *args, **kwargs):
        html = super(DomainWidget, self).render(*args, **kwargs)
        return format_html('<div class="col-sm-4">{}</div>', html)


class FingerprintWidget(BootstrapTextInput):
    input_class = 'gpg-fingerprint'

    class Media:
        js = (
            'account/js/fingerprint_widget.js',
        )


class UsernameWidget(BootstrapWidgetMixin, forms.MultiWidget):
    def decompress(self, value):
        if value:
            return value.split('@', 1)
        return '', settings.DEFAULT_XMPP_HOST

    def render(self, *args, **kwargs):
        widget = forms.MultiWidget.render(self, *args, **kwargs)
        return format_html('<div class="row">{}</div>', widget)

    class Media:
        css = {
            'all': (
                'account/css/username_widget.css',
            ),
        }
        js = (
            'account/js/username_widget.js',
        )
