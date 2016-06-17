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
from django.utils.html import format_html

from . import widgets


class BoundField(forms.boundfield.BoundField):
    def formgroup(self):
        return format_html('<div class="form-group">{}{}</div>', self.label_tag(), self)

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        attrs = attrs or {}
        if 'class' in attrs:
            attrs['class'] += ' control-label col-sm-2'
        else:
            attrs['class'] = 'control-label col-sm-2'

        return super(BoundField, self).label_tag(contents, attrs=attrs, label_suffix=label_suffix)


class BootstrapMixin(object):
    """Mixin that adds the form-control class used by bootstrap to input widgets."""

    def get_bound_field(self, form, field_name):
        return BoundField(form, self, field_name)


class BootstrapCharField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextInput


class BootstrapEmailField(BootstrapMixin, forms.EmailField):
    widget = widgets.BootstrapEmailInput
