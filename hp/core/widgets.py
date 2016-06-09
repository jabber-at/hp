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
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.html import mark_safe

from .constants import TARGET_URL
from .constants import TARGET_NAMED_URL
from .constants import TARGET_MODEL

log = logging.getLogger(__name__)


class LinkTargetWidget(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        self.models = kwargs.pop('models', [])
        super(LinkTargetWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)
        output = ['<div class="linktarget-wrapper">']
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))
            output.append('<div>')
            widget_id = name + '_%s' % i

            # create the label
            if widget.label:
                label_attrs = {'for': widget_id}
                if widget.is_required is True:
                    label_attrs['class'] = 'required'
                label_attrs = flatatt(label_attrs) if label_attrs else ''
                output.append(format_html('<label{}>{}:</label>', label_attrs, widget.label))

            output.append(widget.render(widget_id, widget_value, final_attrs))
            output.append('</div>')

        output.append('</div>')
        return mark_safe(self.format_output(output))

    def decompress(self, value):
        default_model = 1
        if self.models:
            default_model = self.models[0].pk

        if value is None:
            return [TARGET_URL, '', '[]', '{}', default_model, '']

        value = json.loads(value)
        typ = value.get('typ', TARGET_URL)

        if typ == TARGET_URL:
            return [typ, value.get('url', ''), '[]', '{}', default_model, '']
        elif typ == TARGET_NAMED_URL:
            return [typ, value.get('name', ''), value.get('args', '[]'), value.get('kwargs', '{}'),
                    default_model, '']
        elif typ == TARGET_MODEL:
            return [typ, '', '', '', value.get('content_type', 1), value.get('object_id')]
        log.error('Unkown typ %s', typ)
        return [TARGET_URL, '', '[]', '{}', default_model, '']
