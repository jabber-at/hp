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


class BootstrapWidgetMixin(object):
    input_class = None
    """If set, this CSS class will always be added to the input widget."""

    glyphicon = False
    """Set to true to add glyphicon for feedback."""

    def __init__(self, attrs=None, glyphicon=None, **kwargs):
        attrs = attrs or {}
        self._add_class(attrs, 'form-control')
        if glyphicon is not None:
            self.glyphicon = glyphicon

        if self.input_class is not None:
            self._add_class(attrs, self.input_class)

        super(BootstrapWidgetMixin, self).__init__(attrs=attrs, **kwargs)

    def get_context(self, name, value, attrs):
        status = attrs.pop('status', None)
        ctx = super(BootstrapWidgetMixin, self).get_context(name, value, attrs)
        ctx['widget']['status'] = status
        ctx['widget']['has_glyphicon'] = self.glyphicon

        # Add concrete glyphicon if there is a status
        if self.glyphicon:
            if status == 'ok':
                ctx['widget']['glyphicon'] = 'glyphicon-ok'
            elif status == 'error':
                ctx['widget']['glyphicon'] = 'glyphicon-remove'

        return ctx

    def _add_class(self, attrs, cls):
        if attrs.get('class'):
            attrs['class'] += ' %s' % cls
        else:
            attrs['class'] = cls


class BootstrapMultiWidget(BootstrapWidgetMixin, forms.MultiWidget):
    template_name = 'bootstrap/forms/widgets/multiwidget.html'


class BootstrapFieldsetWidget(BootstrapWidgetMixin, forms.MultiWidget):
    template_name = 'bootstrap/forms/widgets/fieldset.html'


class BootstrapTextInput(BootstrapWidgetMixin, forms.TextInput):
    template_name = 'bootstrap/forms/widgets/text.html'


class BootstrapTextarea(BootstrapWidgetMixin, forms.Textarea):
    pass


class BootstrapEmailInput(BootstrapWidgetMixin, forms.EmailInput):
    template_name = 'bootstrap/forms/widgets/text.html'
    input_class = 'valid-email'
    feedback = True
    glyphicon = True

    class Media:
        js = (
            'bootstrap/js/email_input.js',
        )


class BootstrapPasswordInput(BootstrapWidgetMixin, forms.PasswordInput):
    template_name = 'bootstrap/forms/widgets/password.html'
    feedback = True


class BootstrapSelect(BootstrapWidgetMixin, forms.Select):
    input_class = 'custom-select'


class BootstrapFileInput(BootstrapWidgetMixin, forms.ClearableFileInput):
    input_class = 'upload-button'
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
