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

from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import FieldDoesNotExist
from django.forms.renderers import get_default_renderer
from django.forms.utils import flatatt
from django.template.defaultfilters import filesizeformat
from django.utils.functional import Promise
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _

from . import widgets


class BoundField(forms.boundfield.BoundField):
    """Overwrite BoundField to provide customised widget rendering and the formgroup() method.

    A BoundField is a form field in the context of a form.

    .. seealso:: https://docs.djangoproject.com/en/dev/ref/forms/api/#django.forms.BoundField
    """

    def formgroup_attrs(self):
        """HTML attributes for the top-level form-group div."""

        fg_attrs = dict(self.field.formgroup_attrs)
        fg_attrs.setdefault('id', 'fg_%s' % self.html_name)
        if fg_attrs.get('class'):
            fg_attrs['class'] += ' form-group'
        else:
            fg_attrs['class'] = 'form-group'

        if self.field.formgroup_class:
            fg_attrs['class'] += ' %s' % self.field.formgroup_class

        # If the form is bound, we add .was-validated for form validation
        if self.form.is_bound:
            fg_attrs['class'] += ' was-validated'

        if self.horizontal:
            fg_attrs['class'] += ' row'

        errors = self.errors.as_data()
        if errors:
            fg_attrs['class'] += ' form-group-invalid'

        for error in errors:
            if error.code:
                fg_attrs['class'] += ' invalid-%s' % error.code
            else:
                fg_attrs['class'] += ' invalid-default'

        return flatatt(fg_attrs)

    @property
    def horizontal(self):
        return getattr(self.field, 'horizontal', True)

    def get_horizontal_wrapper_attrs(self):
        return self.field.get_horizontal_wrapper_attrs()

    @property
    def help_id(self):
        return 'hb_%s' % self.html_name

    def as_widget(self, *args, **kwargs):
        html = super().as_widget(*args, **kwargs)
        html += self.render_feedback()
        return html

    def build_widget_attrs(self, attrs, widget):
        attrs = super(BoundField, self).build_widget_attrs(attrs, widget)

        min_val_length = getattr(self.field, 'min_validation_length', False)
        if min_val_length is not False:
            attrs['data-min-validation-length'] = str(min_val_length)

        if self.help_text:
            # Add the 'aria-describedby' attribute to the <input /> element. It's the id used by
            # the help-block describing the element and helps screen readers. See:
            #   http://getbootstrap.com/css/#forms-help-text
            attrs['aria-describedby'] = self.help_id

        return attrs

    def render_feedback(self):
        """Render the invalid-feedback messages.

        This tries to get all possible error messages from the model field and form field. The messages are
        used to by CSS to display the correct error message upon submission and by JS during form validation.
        """
        renderer = self.form.renderer or get_default_renderer()

        msg_context = {
            'field_label': self.label,
            'value': self.value(),
        }
        if hasattr(self.field, 'max_length'):
            msg_context['limit_value'] = self.field.max_length
        if hasattr(self.field, 'min_length'):
            msg_context['limit_value'] = self.field.min_length

        if hasattr(self.field, 'get_message_context'):
            msg_context.update(self.field.get_message_context(msg_context['value']))

        invalid = {}

        # get model field validation messages first
        if getattr(self.form, 'instance', None):
            try:
                field = self.form.instance._meta.get_field(self.name)

                # update context for error message formatting
                msg_context['model_name'] = self.form.instance._meta.verbose_name

                # extra field validators
                invalid.update({v.code: v.message for v in field.validators})
                invalid.update(field.error_messages)
            except FieldDoesNotExist:
                pass

        invalid.update({v.code: v.message for v in self.field.validators})

        # Update this with any error messages raised by the field itself.
        invalid.update({k if k else 'default': v for k, v in self.field.error_messages.items()})

        invalid = {k: v % msg_context for k, v in invalid.items() if k in self.field.html_errors}
        invalid.update({e.code: ' '.join(e) for e in self.errors.as_data()})

        context = {
            'field': self,
            'valid': self.field.get_valid_feedback(),
            'invalid': invalid,
        }
        return mark_safe(renderer.render(self.field.feedback_template, context))

    def formgroup(self):
        renderer = self.form.renderer or get_default_renderer()
        context = {'field': self}
        return mark_safe(renderer.render(self.field.formgroup_template, context))

    def get_label_attrs(self):
        return self.field.get_label_attrs()

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        """Add the control-label and col-sm-2 class to label tags."""

        attrs = attrs or {}
        label_attrs = self.get_label_attrs()

        # Handle classes separately, so they are not overwritten
        label_classes = label_attrs.pop('class', None)
        if label_classes:
            if 'class' in attrs:
                attrs['class'] += ' %s' % label_classes
            else:
                attrs['class'] = label_classes

        return super(BoundField, self).label_tag(contents, attrs=attrs, label_suffix=label_suffix)


class BootstrapMixin(object):
    """Mixin that adds the form-control class used by bootstrap to input widgets."""

    formgroup_class = None
    hide_label = False

    # Override error messages so that they contain no values, since they are usually displayed with JavaScript
    default_error_messages = {
        'max_length': _('Ensure this value has at most %(limit_value)d characters.'),
        'min_length': _('Ensure that this value has at least %(limit_value)d characters.'),
    }
    default_html_errors = {
        'invalid',
        'unique',
    }

    horizontal = True
    """Display this field as a horizontal form group."""

    # NOTE: on medium displays sm-2 labels are a bit to small for some usecases ("Username:")
    label_columns = 'col-sm-2 col-md-3 col-lg-2'
    input_columns = 'col-sm-10 col-md-9 col-lg-10'

    min_validation_length = False
    """Start JavaScript validation at the given length."""

    valid_feedback = None

    formgroup_template = 'bootstrap/forms/formgroup.html'
    feedback_template = 'bootstrap/forms/feedback.html'

    def __init__(self, **kwargs):
        self.formgroup_attrs = kwargs.pop('formgroup_attrs', {})

        if 'horizontal' in kwargs:
            self.horizontal = kwargs.pop('horizontal')
        if 'input_columns' in kwargs:
            self.input_columns = kwargs.pop('input_columns')
        if 'label_columns' in kwargs:
            self.label_columns = kwargs.pop('label_columns')

        if 'min_validation_length' in kwargs:
            self.min_validation_length = kwargs.pop('min_validation_length')

        self.valid_feedback = self._handle_feedback('valid_feedback', kwargs)

        html_errors = kwargs.pop('html_errors', set())
        for c in reversed(self.__class__.__mro__):
            html_errors |= getattr(c, 'default_html_errors', set())
        html_errors |= html_errors or set()
        self.html_errors = html_errors

        self.hide_label = kwargs.pop('hide_label', self.hide_label)

        super(BootstrapMixin, self).__init__(**kwargs)

        # Add some HTML errors only if they are applicable to the field
        if self.required:
            self.html_errors.add('required')
        if getattr(self, 'min_length', False):
            self.html_errors.add('min_length')
        if getattr(self, 'max_length', False):
            self.html_errors.add('max_length')

    def _handle_feedback(self, key, kwargs):
        cls_value = getattr(self, key, None)

        # sanitize class attribute
        if cls_value is None:
            cls_value = {}
        if isinstance(cls_value, (Promise, str)):  # Promise == translated string
            cls_value = {'default': cls_value, }
        else:
            cls_value = cls_value.copy()

        value = kwargs.pop(key, {})
        if isinstance(value, (Promise, str)):  # Promise == translated string
            value = {'': value, }
        cls_value.update(value)

        return cls_value

    def get_valid_feedback(self):
        return self.valid_feedback

    def get_horizontal_wrapper_attrs(self):
        return {'class': self.input_columns}

    def get_label_attrs(self):
        """Get attributes for the label tag."""

        return {'class': self.get_label_classes(), }

    def get_label_classes(self):
        """Get classes used for this class."""
        cls = []

        if self.hide_label is True:
            cls.append('sr-only')

        if self.horizontal:
            cls.append(self.get_label_columns())
            cls.append('col-form-label')

        return ' '.join(cls)

    def get_label_columns(self):
        """Get the colum CSS classes used in this form."""

        return self.label_columns

    def get_message_context(self, value):
        """Return additional context for rendering validation errors.

        .. WARNING::

            This method is also called for unbound forms where ``value is None``, but the error messages are
            still formatted. You must always return the required the required keys to make sure there are no
            formatting errors.
        """
        return {}

    def get_bound_field(self, form, field_name):
        return BoundField(form, self, field_name)


class BootstrapCharField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextInput


class BootstrapTextField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapTextarea


class BootstrapEmailField(BootstrapMixin, forms.EmailField):
    widget = widgets.BootstrapEmailInput

    def __init__(self, **kwargs):
        kwargs.setdefault('min_validation_length', 5)
        super().__init__(**kwargs)

    def clean(self, value):
        value = super(BootstrapEmailField, self).clean(value)
        if value:
            value = value.lower()
        return value

    def get_message_context(self, value):
        if not value:
            return {
                'node': '__node__',
                'domain': '__domain__',
            }

        node, domain = value.rsplit('@', 1)
        return {
            'node': node,
            'domain': domain,
        }


class BootstrapPasswordField(BootstrapMixin, forms.CharField):
    widget = widgets.BootstrapPasswordInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', _('Password'))
        super().__init__(*args, **kwargs)


class BootstrapSetPasswordField(BootstrapPasswordField):
    min_validation_length = 2
    widget = widgets.BootstrapSetPasswordInput
    default_error_messages = {
        'min_length': _('Your password must contain at least %(limit_value)d characters.'),
    }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', True)

        # Set the min_length attribute if we have a MinimumLenghtValidator
        for validator in password_validation.get_default_password_validators():
            if isinstance(validator, password_validation.MinimumLengthValidator):
                kwargs.setdefault('min_length', validator.min_length)
                self.min_length = validator.min_length
                break

        kwargs.setdefault('help_text', password_validation.password_validators_help_text_html())

        super().__init__(*args, **kwargs)


class BootstrapConfirmPasswordField(BootstrapPasswordField):
    min_validation_length = 2
    widget = widgets.BootstrapConfirmPasswordInput
    default_error_messages = {
        'no-match': _('The passwords did not match'),
    }
    default_html_errors = {
        'no-match',
    }
    valid_feedback = _('The two passwords match.')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', _('Confirm'))
        kwargs.setdefault('help_text', _('Confirm the password to make sure you spelled it correctly.'))
        super().__init__(*args, **kwargs)


class BootstrapChoiceField(BootstrapMixin, forms.ChoiceField):
    widget = widgets.BootstrapSelect


class BootstrapModelChoiceField(BootstrapMixin, forms.ModelChoiceField):
    widget = widgets.BootstrapSelect


class BootstrapFileField(BootstrapMixin, forms.FileField):
    default_error_messages = {
        'mime-type': _('Upload a file with the correct type.'),
        'too-large': _(
            'Please keep the file size under %(max_size)s. Current file size is %(size)s.'
        ),
    }
    default_html_errors = {
        'mime-type',
        'too-large',
    }
    maximum_file_size = settings.MAX_UPLOAD_SIZE
    widget = widgets.BootstrapFileInput

    def __init__(self, *args, mime_types=None, **kwargs):
        mime_types = set()
        for c in reversed(self.__class__.__mro__):
            mime_types |= getattr(c, 'default_mime_types', set())
        mime_types |= mime_types or set()
        self.mime_types = mime_types

        super().__init__(*args, **kwargs)

    def clean(self, value, initial=None):
        value = super().clean(value, initial=initial)

        if value and value._size > self.maximum_file_size:
            raise forms.ValidationError(self.error_messages['too-large'] % {
                'max_size': filesizeformat(self.maximum_file_size),
                'size': filesizeformat(value._size),
            }, code='too-large')

        if value and self.mime_types and value.content_type not in self.mime_types:
            raise forms.ValidationError(self.error_messages['mime-type'] % {
                'value': value.content_type,
            }, code='mime-type')
        return value

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        if self.maximum_file_size:
            attrs['data-maxsize'] = self.maximum_file_size

        # NOTE: Nothing matches GPG keys, so don't add the "accept" HTML5 form validation attribute here
        #if self.mime_types:
        #    attrs['accept'] = ','.join(self.mime_types)

        return attrs

    def get_message_context(self, value):
        return {
            # NOTE: messages in this field are never displayed by JavaScript, so it's ok to have no value
            #       on initial load.
            'size': value._size if value else '__size__',
            'max_size': filesizeformat(self.maximum_file_size),
        }


class BootstrapBooleanField(BootstrapMixin, forms.BooleanField):
    widget = widgets.BootstrapCheckboxInput

    def __init__(self, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(**kwargs)

    def get_label_attrs(self):
        return {'class': 'form-check-label', }
