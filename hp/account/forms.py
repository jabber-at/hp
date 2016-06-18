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

from core.forms import CaptchaFormMixin

from .models import User
from .formfields import UsernameField
from .formfields import FingerprintField
from .formfields import KeyUploadField

_MIN_USERNAME_LENGTH = getattr(settings, 'MIN_USERNAME_LENGTH', 2)
_MAX_USERNAME_LENGTH = getattr(settings, 'MAX_USERNAME_LENGTH', 64)


class GPGMixin(forms.Form):
    """A mixin that adds the GPG fields to a form."""

    if getattr(settings, 'GPG', True):
        #fingerprint = XMPPAccountFingerprintField()
        gpg_fingerprint = FingerprintField()
        gpg_key = KeyUploadField()

    def gpg_options(self, request):
        if not getattr(settings, 'GPG', True):
            return {}

        if self.cleaned_data.get('fingerprint'):
            return {'gpg_encrypt': self.cleaned_data.get('fingerprint'), }
        elif 'gpg_key' in request.FILES:
            path = request.FILES['gpg_key'].temporary_file_path()
            with open(path) as stream:
                data = stream.read()
            return {'gpg_key': data, }
        return {}

    class Media:
        js = (
            'xmpp_accounts/js/gpgmixin.js',
        )


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


class SetPasswordForm(forms.Form):
    password = BootstrapPasswordField()
    password2 = BootstrapPasswordField()

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
