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
from django.utils.translation import ugettext_lazy as _

from bootstrap.widgets import BootstrapMultiWidget
from bootstrap.widgets import BootstrapTextInput


class NodeWidget(BootstrapTextInput):
    """The widget used for rendering the node part (before the "@") of a username.

    This class is used because we want to render this widget in a bootstrap column.
    """

    def __init__(self, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs['pattern'] = '[^@ ]{%s,%s}' % (settings.MIN_USERNAME_LENGTH,
                                             settings.MAX_USERNAME_LENGTH)
        #attrs['title'] = _('At least 2 characters, no "@" or spaces.')
        super(NodeWidget, self).__init__(attrs=attrs, **kwargs)

    def build_attrs(self, *args, **kwargs):
        attrs = super(NodeWidget, self).build_attrs(*args, **kwargs)
        attrs['title'] = _(
            'At least %(MIN_LENGTH)s and up to %(MAX_LENGTH)s characters. No "@" or spaces.') % {
            'MIN_LENGTH': settings.MIN_USERNAME_LENGTH,
            'MAX_LENGTH': settings.MAX_USERNAME_LENGTH,
        }
        return attrs

    def render(self, *args, **kwargs):
        html = super(NodeWidget, self).render(*args, **kwargs)
        return format_html('<div class="col-sm-8">{}</div>', html)


class DomainWidget(forms.Select):
    """The widget used for rendering the domain part of a username."""

    def render(self, name, value, attrs):
        # If there is just one choice, we set the 'disabled' property to the select widget. Since
        # "disabled" widgets are not submitted, we add an additional hidden input with the correct
        # name.
        if len(self.choices) == 1:
            attrs['disabled'] = 'disabled'
            html = super(DomainWidget, self).render('', value, attrs)
            html += forms.HiddenInput().render(name, self.choices[0][0], {})
        else:
            html = super(DomainWidget, self).render(name, value, attrs)

        return format_html('<div class="col-sm-4">{}</div>', html)


class FingerprintWidget(BootstrapTextInput):
    input_class = 'gpg-fingerprint'
    feedback = True
    glyphicon = True

    def __init__(self, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs['pattern'] = '[0-9A-Fa-f ]{40,50}'
        attrs['title'] = _(
            'The hex-encoded value of the fingerprint: digits, letters A-F (case-insensitive).')
        super(FingerprintWidget, self).__init__(attrs=attrs, **kwargs)

    class Media:
        js = (
            'account/js/fingerprint_widget.js',
        )


class UsernameWidget(BootstrapMultiWidget):
    feedback = True

    def decompress(self, value):
        if value:
            return value.lower().split('@', 1)
        return '', settings.DEFAULT_XMPP_HOST

    def render(self, *args, **kwargs):
        widget = super(UsernameWidget, self).render(*args, **kwargs)
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
