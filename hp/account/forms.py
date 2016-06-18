# -*- coding: utf-8 -*-
#
# This file is part of xmpp-backends (https://github.com/mathiasertl/xmpp-backends).
#
# xmpp-backends is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# xmpp-backends is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with xmpp-backends.  If
# not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from bootstrap.formfields import BootstrapEmailField
from bootstrap.formfields import BootstrapPasswordField

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

    class Media:
        js = (
            'xmpp_accounts/js/gpgmixin.js',
        )


class CreateUserForm(GPGMixin, forms.ModelForm):
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


class LoginForm(AuthenticationForm):
    username = UsernameField()
    password = BootstrapPasswordField()


class CreateUserConfirmationForm(forms.Form):
    pass


class ResetPasswordForm(forms.Form):
    pass


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
