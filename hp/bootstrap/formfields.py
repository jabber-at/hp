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
from django.forms.utils import flatatt
from django.utils.html import format_html
from django.utils.html import mark_safe

from . import widgets


class BoundField(forms.boundfield.BoundField):
    def formgroup(self):
        help_text = ''
        if self.help_text or self.errors:
            help_text = format_html('<p id="{}" class="help-block">{}{}</p>', self.help_id,
                                    self.help_text, self.errors)

        fg_attrs = dict(self.field.formgroup_attrs)
        fg_attrs.setdefault('id', 'fg_%s' % self.html_name)
        if fg_attrs.get('class'):
            fg_attrs['class'] += ' form-group'
        else:
            fg_attrs['class'] = 'form-group'

        icon_classes = 'glyphicon form-control-feedback'

        if self.errors:
            fg_attrs['class'] += ' has-error'
            icon_classes += ' glyphicon-remove'
        elif self.form.is_bound and not self.errors:
            # TODO: maybe not add this class if the field is optional and no text was entered?
            fg_attrs['class'] += ' has-success'
            icon_classes += ' glyphicon-ok'

        feedback_icons = ''
        if getattr(self.field.widget, 'feedback', False):
            fg_attrs['class'] += ' has-feedback'
            feedback_icons = mark_safe(
                '<span class="%s" aria-hidden="true"></span>' % icon_classes)

        return format_html('<div {}>{}<div class="col-sm-10 foo">{}{}{}</div></div>', flatatt(fg_attrs),
                           self.label_tag(), self, feedback_icons, help_text)

    @property
    def help_id(self):
        return 'hb_%s' % self.html_name

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        attrs = attrs or {}
        if self.help_text or self.errors:
            # Add the 'aria-describedby' attribute to the <input /> element. It's the id used by
            # the help-block describing the element and helps scree readers. See:
            #   http://getbootstrap.com/css/#forms-help-text
            attrs['aria-describedby'] = self.help_id

        return super(BoundField, self).as_widget(widget=widget, attrs=attrs,
                                                 only_initial=only_initial)

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        attrs = attrs or {}
        if 'class' in attrs:
            attrs['class'] += ' control-label col-sm-2'
        else:
            attrs['class'] = 'control-label col-sm-2'

        return super(BoundField, self).label_tag(contents, attrs=attrs, label_suffix=label_suffix)


class BootstrapMixin(object):
    """Mixin that adds the form-control class used by bootstrap to input widgets."""

    def __init__(self, **kwargs):
        self.formgroup_attrs = kwargs.pop('formgroup_attrs', {})
        super(BootstrapMixin, self).__init__(**kwargs)

    def get_bound_field(self, form, field_name):
        return BoundField(form, self, field_name)


class BootstrapCharField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextInput


class BootstrapEmailField(BootstrapMixin, forms.EmailField):
    widget = widgets.BootstrapEmailInput


class BootstrapPasswordField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapPasswordInput


class BootstrapFileField(BootstrapMixin, forms.FileField):
    widget = widgets.BootstrapFileInput
