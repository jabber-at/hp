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

from bootstrap.widgets import BootstrapEmailInput
from bootstrap.widgets import BootstrapMultiWidget
from bootstrap.widgets import BootstrapSelect
from bootstrap.widgets import BootstrapTextInput
from bootstrap.widgets import MergeClassesMixin


class NodeWidget(MergeClassesMixin, BootstrapTextInput):
    """The widget used for rendering the node part (before the "@") of a username.

    This class is used because we want to render this widget in a bootstrap column.
    """

    css_classes = 'mb-2 mb-md-0'

    def __init__(self, attrs=None, **kwargs):
        attrs = attrs or {}
        # NOTE: Do not give a range ("{2,64}" here, because otherwise HTML5 validation will always show
        #       pattern mismatch and never tooShort as error.
        attrs['pattern'] = '[^@ ]+'
        self.register = kwargs.pop('register', False)
        super(NodeWidget, self).__init__(attrs=attrs, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)

        if self.register:
            attrs['data-check-existance'] = 'true'

        return attrs


class DomainWidget(BootstrapSelect):
    """The widget used for rendering the domain part of a username."""

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs['class'] += ' custom-select'
        return attrs


class FingerprintWidget(BootstrapTextInput):
    css_classes = 'gpg-fingerprint'


class UsernameWidget(BootstrapMultiWidget):
    template_name = "account/widgets/username.html"

    def decompress(self, value):
        if value:
            return value.lower().split('@', 1)
        return '', settings.DEFAULT_XMPP_HOST

    class Media:
        css = {
            'all': (
                'account/css/username_widget.css',
            ),
        }
        js = (
            'account/js/username_widget.js',
        )


class EmailVerifiedDomainWidget(BootstrapEmailInput):
    class Media:
        css = {
            'all': (
                'account/css/email_verified_domain_widget.css',
            ),
        }
        js = (
            'account/js/email_verified_domain_widget.js',
        )
