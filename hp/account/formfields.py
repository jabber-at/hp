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

import dns.resolver

from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bootstrap.formfields import BootstrapCharField
from bootstrap.formfields import BootstrapEmailField
from bootstrap.formfields import BootstrapFileField
from bootstrap.formfields import BootstrapMixin

from .widgets import DomainWidget
from .widgets import NodeWidget
from .widgets import UsernameWidget
from .widgets import FingerprintWidget


class UsernameField(BootstrapMixin, forms.MultiValueField):
    formgroup_class = 'form-group-username'

    def __init__(self, **kwargs):
        self.register = kwargs.pop('register', False)
        self.status_check = kwargs.pop('status_check', self.register)
        kwargs.setdefault('label', _('Username'))

        hosts = getattr(settings, 'XMPP_HOSTS', {})
        if self.register is True:
            hosts = [k for k, v in hosts.items()
                     if v.get('REGISTRATION') and v.get('MANAGE', True)]
        else:
            hosts = [k for k, v in hosts.items() if v.get('MANAGE', True)]
        choices = tuple([(d, '@%s' % d) for d in hosts])

        fields = (
            forms.CharField(
                widget=NodeWidget(glyphicon=self.register),
                min_length=settings.MIN_USERNAME_LENGTH,
                max_length=settings.MAX_USERNAME_LENGTH,
                error_messages={
                    'min_length': _('Username must have at least %(limit_value)d characters.'),
                    'max_length': _('Username must have at most %(limit_value)d characters.'),
                },
                validators=[
                    RegexValidator(r'^[^@\s]+$', _('Username contains invalid characters.')),
                ],
            ),
            forms.ChoiceField(initial=settings.DEFAULT_XMPP_HOST,
                              choices=choices, widget=DomainWidget),
        )
        widgets = [f.widget for f in fields]

        attrs = {}
        if self.register is True:
            attrs['class'] = 'status-check'
        else:
            # Do not add the has-success class in forms other then the registration form
            kwargs.setdefault('add_success', False)

        self.widget = UsernameWidget(widgets=widgets, attrs=attrs)
        super(UsernameField, self).__init__(fields=fields, require_all_fields=True, **kwargs)

    def get_help_text(self):
        if self.register is True:
            help_text = _(
                'At least %(MIN_LENGTH)s and up to %(MAX_LENGTH)s characters. No "@" or spaces.'
            ) % {
                'MIN_LENGTH': settings.MIN_USERNAME_LENGTH,
                'MAX_LENGTH': settings.MAX_USERNAME_LENGTH,
            }

            default = format_html('<span id="default">{}</span>',
                                  _('Type to see if the username is still available.'))
            available = format_html('<span id="username-available">{}</span>',
                                    _('The username is still available.'))
            not_available = format_html('<span id="username-not-available">{}</span>',
                                        _('The username is no longer available.'))
            invalid = format_html('<span id="invalid">{}</span>',
                                  _('The username is invalid.'))
            error = format_html('<span id="error">{}</span>',
                                _('An error occured, please try again later.'))
            return format_html(
                '''{}<span class="help-block" id="status-check">{}{}{}{}{}</span>''',
                help_text, default, available, not_available, invalid, error)
        return ''

    def compress(self, data_list):
        node, domain = data_list
        node = node.lower()
        return '@'.join(data_list)


class FingerprintField(BootstrapCharField):
    widget = FingerprintWidget

    def __init__(self, **kwargs):
        # "gpg --list-keys --fingerprint" outputs fingerprint with spaces, making it 50 chars long
        kwargs.setdefault('label', _('Fingerprint'))
        kwargs.setdefault('max_length', 50)
        kwargs.setdefault('min_length', 40)
        kwargs.setdefault('required', False)
        kwargs.setdefault('help_text', _(
            'Add your fingerprint (<code>gpg --fingerprint &lt;you@example.com&gt;</code>) if '
            'your key is available on public key servers...'))

        # define error messages
        kwargs.setdefault('error_messages', {})
        kwargs['error_messages'].setdefault('not-enabled', _('GPG not enabled.'))
        kwargs['error_messages'].setdefault('invalid-length',
                                            _('Fingerprint should be 40 characters long.'))
        kwargs['error_messages'].setdefault('invalid-chars',
                                            _('Fingerprint contains invalid characters.'))
        super(FingerprintField, self).__init__(**kwargs)

    def clean(self, value):
        if not getattr(settings, 'GPG_BACKENDS', {}):  # check, just to be sure
            raise forms.ValidationError(self.error_messages['not-enabled'])

        fp = super(FingerprintField, self).clean(value).strip().replace(' ', '').upper()
        if fp == '':
            return None  # no fingerprint given
        if len(fp) != 40:
            raise forms.ValidationError(self.error_messages['invalid-length'])
        if re.search('[^A-F0-9]', fp) is not None:
            raise forms.ValidationError(self.error_messages['invalid-chars'])

        return fp


class KeyUploadField(BootstrapFileField):
    def __init__(self, **kwargs):
        kwargs.setdefault('required', False)
        kwargs.setdefault('label', _('GPG Key'))
        kwargs.setdefault('help_text', _(
            '... upload your ASCII armored GPG key directly '
            '(<code>gpg --armor --export &lt;fingerprint&gt;</code>).'
        ))

        # define error messages
        kwargs.setdefault('error_messages', {})
        kwargs['error_messages'].setdefault('not-enabled', _('GPG not enabled.'))
        kwargs['error_messages'].setdefault(
            'invalid-filetype', _('Only plain-text files are allowed (was: %(content-type)s)!'))
        super(KeyUploadField, self).__init__(**kwargs)

    def clean(self, value, initial):
        if not getattr(settings, 'GPG_BACKENDS', {}):  # check, just to be sure
            raise forms.ValidationError(self.error_messages['not-enabled'])

        gpg_key = super(KeyUploadField, self).clean(value)

        if not gpg_key:
            return gpg_key
        if gpg_key.content_type not in ['text/plain', 'application/pgp-encrypted']:
            raise forms.ValidationError(self.error_messages['invalid-filetype'] % {
                'content-type': gpg_key.content_type,
            })

        return value


class EmailVerifiedDomainField(BootstrapEmailField):
    """An email formfield that verifies that the domain actually exists.

    Parameters
    ----------

    verify_domain : bool, optional
        Pass ``False`` if you don't want to verify the domain. If you do, this class
        behaves no differently then its parent class.
    kwargs
        All passed to the parent class.
    """
    def __init__(self, verify_domain=True, **kwargs):
        self._verify_domain = verify_domain
        if verify_domain is True:
            kwargs.setdefault('error_messages', {})
            kwargs['error_messages'].setdefault(
                'domain-does-not-exist', _('The domain "%(domain)s" does not exist.'))

        super(EmailVerifiedDomainField, self).__init__(**kwargs)

    def clean(self, *args, **kwargs):
        email = super(EmailVerifiedDomainField, self).clean(*args, **kwargs)
        if not email:
            return email

        _node, domain = email.rsplit('@', 1)
        if domain and self._verify_domain:
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
                    'domain': domain,
                })
        return email
