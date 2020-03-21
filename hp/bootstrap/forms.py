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

from django.forms.renderers import get_default_renderer
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class BootstrapFormMixin(object):
    """Mixin for Bootstrap forms, making (some) variables globally overridable."""

    button_template = 'bootstrap/forms/buttons.html'
    button_order = ['submit']
    default_buttons = {
        'submit': {
            'text': _('Submit'),
            'class': 'primary',
        },
    }
    input_columns = None
    label_columns = None

    # offset for elements that don't have a label column, e.g. the submit buttons.
    # NOTE: This should match label_columns from the field forms
    offset_columns = 'col-sm-9 offset-sm-2 offset-md-3 offset-lg-2'

    def __init__(self, *args, input_columns=None, label_columns=None, offset_columns=None, **kwargs):
        if offset_columns is not None:
            self.offset_columns = offset_columns
        if 'button_order' in 'kwargs':
            self.button_order = kwargs.pop('button_order')
        if 'button_template' in 'kwargs':
            self.button_template = kwargs.pop('button_template')

        super().__init__(*args, **kwargs)

        input_columns = input_columns or self.input_columns
        if input_columns is not None:
            for key, field in self.fields.items():
                field.input_columns = input_columns

        label_columns = label_columns or self.label_columns
        if label_columns is not None:
            for key, field in self.fields.items():
                field.label_columns = label_columns

        buttons = {}
        for c in reversed(self.__class__.__mro__):
            buttons.update(getattr(c, 'default_buttons', {}))
        buttons.update(kwargs.pop('buttons', {}))
        self._buttons = buttons

    def get_button_order(self):
        return self.button_order

    def buttons(self):
        renderer = self.renderer or get_default_renderer()
        order = self.get_button_order()
        buttons = sorted(self._buttons.items(), key=lambda t: order.index(t[0]) if t[0] in order else -1)

        context = {'buttons': buttons, 'form': self}
        return mark_safe(renderer.render(self.button_template, context))

    def get_offset_columns(self):
        return self.offset_columns
