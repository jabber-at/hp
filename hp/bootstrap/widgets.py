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
from django.utils.html import mark_safe
from django.utils.translation import ugettext as _


class BootstrapWidgetMixin(object):
    input_class = None

    def __init__(self, attrs=None, **kwargs):
        attrs = attrs or {}
        self._add_class(attrs, 'form-control')

        if self.input_class is not None:
            self._add_class(attrs, self.input_class)

        super(BootstrapWidgetMixin, self).__init__(attrs=attrs, **kwargs)

    def _add_class(self, attrs, cls):
        if attrs.get('class'):
            attrs['class'] += ' %s' % cls
        else:
            attrs['class'] = cls

    def render(self, *args, **kwargs):
        widget = super(BootstrapWidgetMixin, self).render(*args, **kwargs)
        return format_html('<div class="col-sm-10">{}</div>', widget)


class BootstrapTextInput(BootstrapWidgetMixin, forms.TextInput):
    pass


class BootstrapEmailInput(BootstrapWidgetMixin, forms.EmailInput):
    input_class = 'valid-email'

    class Media:
        js = (
            'bootstrap/js/email_input.js',
        )

class BootstrapPasswordInput(BootstrapWidgetMixin, forms.PasswordInput):
    pass


class BootstrapFileInput(BootstrapWidgetMixin, forms.ClearableFileInput):
    input_class = 'upload-button'

    def render(self, *args, **kwargs):
        widget = forms.ClearableFileInput.render(self, *args, **kwargs)
        button = format_html('<span class="btn btn-primary" type="span">{}{}</span>',
                             _('Browse...'), widget)
        button = format_html('<label class="input-group-btn">{}</label>', button)

        text_input = mark_safe('<input type="text" class="form-control" readonly>')
        return format_html(
            '<div class="col-sm-10"><div class="input-group">{}{}</div></div>', button, text_input)

    class Media:
        css = {
            'all': (
                'bootstrap/css/file_input.css',
            ),
        }
        js = (
            'bootstrap/js/file_input.js',
        )
