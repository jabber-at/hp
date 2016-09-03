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
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from bootstrap.formfields import BootstrapEmailField
from bootstrap.formfields import BootstrapPasswordField
from bootstrap.widgets import BootstrapPasswordInput

from core.forms import CaptchaFormMixin

from .models import User
from .formfields import UsernameField
from .formfields import FingerprintField
from .formfields import KeyUploadField

_MIN_USERNAME_LENGTH = getattr(settings, 'MIN_USERNAME_LENGTH', 2)
_MAX_USERNAME_LENGTH = getattr(settings, 'MAX_USERNAME_LENGTH', 64)


class GPGMixin(forms.Form):
    """A mixin that adds the GPG fields to a form."""

    if getattr(settings, 'GPG_BACKENDS', {}):
        gpg_fingerprint = FingerprintField()
        gpg_key = KeyUploadField()

    def get_gpg_data(self):
        """Get fingerprint and uploaded key, if any."""

        if not getattr(settings, 'GPG_BACKENDS', {}):  # Shortcut
            return None, None

        fp = self.cleaned_data.get('gpg_fingerprint') or None
        key = None
        if 'gpg_key' in self.files:
            # TODO: Django docs say we should read in chuncks to ensure that large files
            #       don't overwhelm our systems memory. But we need the data in memory anyway.
            #       We should probably enforce a maximum content-length elsewhere.
            key = self.files['gpg_key'].read().decode('utf-8')

        return fp, key

    @property
    def show_gpg(self):
        """Returns True if the user submitted a GPG fingerprint or key to this form.

        Used to decide if the template should display the GPG chapter or not.
        """

        if not self.is_bound or not getattr(settings, 'GPG_BACKENDS', True):
            # Form was not submitted or GPG is not configured
            return False

        if self.get('gpg_fingerprint') or self.files.get('gpg_key'):
            return True
        return False

    class Media:
        js = (
            'account/js/gpgmixin.js',
        )
        css = {
            'all': (
                'account/css/gpgmixin.css',
            ),
        }


class CreateUserForm(GPGMixin, CaptchaFormMixin, forms.ModelForm):
    username = UsernameField(
        register=True,
        help_text=_('At least %(MIN_LENGTH)s and up to %(MAX_LENGTH)s characters. No "@" or spaces.') % {
            'MIN_LENGTH': _MIN_USERNAME_LENGTH,
            'MAX_LENGTH': _MAX_USERNAME_LENGTH,
        }
    )
    email = BootstrapEmailField(
        help_text=_('Required, a confirmation email will be sent to this address.')
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'gpg_fingerprint']


class LoginForm(CaptchaFormMixin, AuthenticationForm):
    username = UsernameField()
    password = BootstrapPasswordField()


class SetPasswordForm(CaptchaFormMixin, forms.Form):
    password = BootstrapPasswordField(
        min_length=6, widget=BootstrapPasswordInput(glyphicon=True),
        help_text=_('Passwords must be at least six characters.'))
    password2 = BootstrapPasswordField(
        min_length=6, widget=BootstrapPasswordInput(glyphicon=True), label=_('Confirm'),
        help_text=_('Confirm the password to make sure you spelled it correctly.'))

    password_error_messages = {
        'password_mismatch': _("The two password fields didn't match.")
    }

    def clean(self):
        cleaned_data = super(SetPasswordForm, self).clean()

        password1 = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        if password1 and password2:
            if password1 != password2:
                self.add_error('password2', self.password_error_messages['password_mismatch'])

    class Media:
        js = (
            'account/js/set_password.js',
        )


class SetEmailForm(GPGMixin, forms.Form):
    email = BootstrapEmailField(
        help_text=_('Required, an email will be sent to this address to confirm the change.')
    )



class RequestPasswordResetForm(CaptchaFormMixin, forms.Form):
    """Form used when a user forgot his password and forgot it."""

    username = UsernameField()


class ResetPasswordConfirmationForm(forms.Form):
    pass


class ResetEmailForm(forms.Form):
    pass


class ResetEmailConfirmationForm(forms.Form):
    pass


class DeleteForm(forms.Form):
    pass


class DeleteConfirmationForm(forms.Form):
    pass
