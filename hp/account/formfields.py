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

import re

import dns.resolver

from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from bootstrap.formfields import BootstrapCharField
from bootstrap.formfields import BootstrapEmailField
from bootstrap.formfields import BootstrapFileField
from bootstrap.formfields import BootstrapMixin

from .widgets import DomainWidget
from .widgets import EmailVerifiedDomainWidget
from .widgets import FingerprintWidget
from .widgets import NodeWidget
from .widgets import UsernameWidget


class UsernameField(BootstrapMixin, forms.MultiValueField):
    formgroup_class = 'form-group-username'
    default_error_messages = {
        'invalid': _('Username cannot contain "@" or spaces.'),
        'max_length': _('Username must have at most %(max_length)s characters.') % {
            'max_length': settings.MAX_USERNAME_LENGTH,
        },
        'min_length': _('Username must have at least %(min_length)s characters.') % {
            'min_length': settings.MIN_USERNAME_LENGTH,
        },
        'exists': _('This username is already taken.'),
        'error': _('Could not check if the username already exists: Error communicating with the server.'),
    }

    # We need to add them here because min/max_length are only set for the CharField
    default_html_errors = {
        'min_length',
        'max_length',
    }

    def __init__(self, **kwargs):
        self.register = kwargs.pop('register', False)
        kwargs.setdefault('label', _('Username'))
        char_kwargs = {}

        if self.register is True:
            choices = tuple([(d, d) for d in settings.REGISTER_HOSTS.keys()])
            char_kwargs['min_length'] = settings.MIN_USERNAME_LENGTH
            char_kwargs['max_length'] = settings.MAX_USERNAME_LENGTH

            # pass through any error messages that may be raised by the CharFields clean() method.
            # Without this, the effective error-message of the field will be an empty string, for some reason.
            char_kwargs['error_messages'] = {
                'min_length': self.default_error_messages['min_length'],
                'max_length': self.default_error_messages['max_length'],
            }
        else:
            choices = tuple([(d, d) for d in settings.MANAGED_HOSTS.keys()])

        if 'help_text' not in kwargs:
            if self.register is True:
                kwargs['help_text'] = _("Your username is used to identify you on the Jabber network.")

        fields = (
            forms.CharField(
                widget=NodeWidget(register=self.register),
                validators=[
                    RegexValidator(r'^[^@\s]+$', self.default_error_messages['invalid'], code='invalid'),
                ],
                **char_kwargs
            ),
            forms.ChoiceField(initial=settings.DEFAULT_XMPP_HOST,
                              choices=choices, widget=DomainWidget),
        )
        widgets = [f.widget for f in fields]

        self.widget = UsernameWidget(widgets=widgets, attrs={})
        super().__init__(fields=fields, require_all_fields=True, **kwargs)

    def compress(self, data_list):
        node, domain = data_list
        node = node.lower()
        return '@'.join(data_list)


class FingerprintField(BootstrapCharField):
    # TODO: Currently shows valid key if between 40 and 50 characers. Could check this with Javascript

    widget = FingerprintWidget
    invalid_feedback = _('Please enter a valid GPG key fingerprint.')
    default_error_messages = {
        'invalid': _(
            'A Fingerprint consists of 40 characters (excluding spaces) and contain only digits, the letters '
            'A-F and spaces.'),
    }

    def __init__(self, **kwargs):
        # "gpg --list-keys --fingerprint" outputs fingerprint with spaces, making it 50 chars long
        kwargs.setdefault('label', _('Fingerprint'))
        kwargs.setdefault('required', False)
        kwargs.setdefault('help_text', _(
            'Add your fingerprint (<code>gpg --fingerprint &lt;you@example.com&gt;</code>) if '
            'your key is available on public key servers...'))
        super().__init__(**kwargs)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)

        # We do set min/maxlength here instead of in the constructor.  This way, our clean method
        # can catch this and throw the invalid error code instead of the custom Django ones.
        attrs['minlength'] = 40
        attrs['maxlength'] = 50
        attrs['pattern'] = '[0-9A-Fa-f ]+'
        attrs['title'] = _(
            'The hex-encoded value of the fingerprint: digits, letters A-F (case-insensitive).')
        return attrs

    def clean(self, value):
        if not getattr(settings, 'GPG_BACKENDS', {}):  # check, just to be sure
            raise forms.ValidationError(self.error_messages['not-enabled'])

        fp = super().clean(value).strip().replace(' ', '').upper()
        if fp == '':
            return None  # no fingerprint given
        elif len(fp) != 40 or re.search('[^A-F0-9]', fp):
            raise forms.ValidationError(self.error_messages['invalid'], code='invalid')

        return fp


class KeyUploadField(BootstrapFileField):
    default_error_messages = {
        'not-enabled': _('GPG not enabled.'),
    }
    default_mime_types = {'text/plain', 'application/pgp-encrypted', 'application/pgp-keys', }

    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('label', _('GPG Key'))
        kwargs.setdefault('help_text', _(
            '... upload your ASCII armored GPG key directly (<code>gpg --armor --export '
            '&lt;fingerprint&gt;</code>).'))

        # define error messages
        super().__init__(**kwargs)

    def clean(self, value, initial=None):
        # This check is just to be sure
        if not getattr(settings, 'GPG_BACKENDS', {}):
            raise forms.ValidationError(self.error_messages['not-enabled'], code='not-enabled')

        return super().clean(value, initial=None)


class EmailVerifiedDomainField(BootstrapEmailField):
    """An email formfield that verifies that the domain actually exists.

    Parameters
    ----------

    kwargs
        All passed to the parent class.
    """
    default_error_messages = {
        'domain-does-not-exist': _('The domain "%(value)s" does not exist.'),
    }
    default_html_errors = {
        'domain-does-not-exist',
    }
    widget = EmailVerifiedDomainWidget

    def clean(self, *args, **kwargs):
        email = super().clean(*args, **kwargs)
        if not email:
            return email

        _node, domain = email.rsplit('@', 1)
        if domain:
            exists = False
            resolver = dns.resolver.Resolver()

            for typ in ['A', 'AAAA', 'MX']:
                try:
                    resolver.query(domain, typ)
                    exists = True
                    break
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    continue

            if exists is False:
                raise forms.ValidationError(self.error_messages['domain-does-not-exist'] % {
                    'value': domain,
                }, code='domain-does-not-exist')
        return email
