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

import re
from collections import OrderedDict

from django import forms


class BootstrapWidgetMixin(object):
    css_classes = ''
    """CSS classes to be added to this element."""

    def __init__(self, attrs=None, css_classes='', **kwargs):
        attrs = attrs or {}
        self._add_class(attrs, 'form-control')

        # handle css_classes
        for cls in self.__class__.mro():
            css_classes += ' %s' % getattr(cls, 'css_classes', '')
        css_classes = re.sub(' +', ' ', css_classes).strip()
        if css_classes:
            self._add_class(attrs, css_classes)

        super(BootstrapWidgetMixin, self).__init__(attrs=attrs, **kwargs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs=extra_attrs)
        self._clean_classes(attrs)
        return attrs

    def _clean_classes(self, attrs):
        if not attrs.get('class'):
            return
        css_classes = re.sub(' +', ' ', attrs['class']).strip()
        attrs['class'] = ' '.join(list(OrderedDict.fromkeys(css_classes.split())))

    def _add_class(self, attrs, cls):
        if attrs.get('class'):
            attrs['class'] += ' %s' % cls
        else:
            attrs['class'] = cls


class MergeClassesMixin(object):
    """Mixin to merge CSS classes from runtime and from the instances class attributes.

    This is most commonly used in MultiWidgets children, where extra_args contains the CSS classes from the
    parent widget.
    """

    def build_attrs(self, base_attrs, extra_attrs=None):
        if extra_attrs is None or 'class' not in base_attrs or 'class' not in extra_attrs:
            return super().build_attrs(base_attrs, extra_attrs=extra_attrs)

        extra_attrs['class'] = '%s %s' % (base_attrs.pop('class', ''), extra_attrs.pop('class', ''))
        return super().build_attrs(base_attrs, extra_attrs=extra_attrs)


class BootstrapMultiWidget(BootstrapWidgetMixin, forms.MultiWidget):
    template_name = 'bootstrap/forms/widgets/multiwidget.html'


class BootstrapTextInput(BootstrapWidgetMixin, forms.TextInput):
    template_name = 'bootstrap/forms/widgets/text.html'


class BootstrapTextarea(BootstrapWidgetMixin, forms.Textarea):
    pass


class BootstrapEmailInput(BootstrapWidgetMixin, forms.EmailInput):
    template_name = 'bootstrap/forms/widgets/text.html'


class BootstrapPasswordInput(BootstrapWidgetMixin, forms.PasswordInput):
    template_name = 'bootstrap/forms/widgets/password.html'


class BootstrapSelect(BootstrapWidgetMixin, forms.Select):
    css_classes = 'custom-select'


class BootstrapFileInput(BootstrapWidgetMixin, forms.ClearableFileInput):
    css_classes = 'upload-button'
    template_name = 'bootstrap/forms/widgets/clearable_file_input.html'

    class Media:
        css = {
            'all': (
                'bootstrap/css/file_input.css',
            ),
        }
        js = (
            'bootstrap/js/file_input.js',
        )
