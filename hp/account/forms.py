# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the
# GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or
# (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If
# not, see
# <http://www.gnu.org/licenses/>.

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminEmailInputWidget
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm as PasswordChangeFormBase
from django.contrib.auth.forms import SetPasswordForm as SetPasswordFormBase
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from bootstrap.formfields import BootstrapBooleanField
from bootstrap.formfields import BootstrapConfirmPasswordField
from bootstrap.formfields import BootstrapPasswordField
from bootstrap.formfields import BootstrapSetPasswordField
from bootstrap.forms import BootstrapFormMixin
from core.forms import CaptchaFormMixin

from .constants import PURPOSE_REGISTER
from .constants import REGISTRATION_MANUAL
from .formfields import EmailVerifiedDomainField
from .formfields import FingerprintField
from .formfields import KeyUploadField
from .formfields import UsernameAdminField
from .formfields import UsernameField
from .models import Notifications
from .models import User
from .tasks import send_confirmation_task

_GPG_ENABLED = bool(settings.GPG_BACKENDS)


class GPGMixin(forms.Form):
    """A mixin that adds the GPG fields to a form."""

    if _GPG_ENABLED is True:
        gpg_fingerprint = FingerprintField(horizontal=True)
        gpg_key = KeyUploadField(horizontal=True)

        input_columns = 'col-12 col-lg-10'
        label_columns = 'col-12 col-lg-2'
        offset_columns = 'col-12 col-lg-10 offset-lg-2'

    def get_gpg_data(self):
        """Get fingerprint and uploaded key, if any."""

        if _GPG_ENABLED is False:  # Shortcut
            return None, None

        fp = self.cleaned_data.get('gpg_fingerprint') or None
        key = None
        if 'gpg_key' in self.files:
            key = self.files['gpg_key'].read().decode('utf-8').strip()

        return fp, key

    @property
    def show_gpg(self):
        return _GPG_ENABLED

    @property
    def hide_gpg_content(self):
        """True if GPG content should be hidden.

        The content is hidden if the form is not bound (= initial page call) or if the user did not
        submit any GPG data.
        """
        if not self.is_bound:
            return True
        if self.data.get('gpg_fingerprint') or self.files.get('gpg_key'):
            return False
        return True

    class Media:
        js = (
            'account/js/gpgmixin.js',
        )
        css = {
            'all': (
                'account/css/gpgmixin.css',
            ),
        }


class EmailValidationMixin(object):
    """Mixin that validates the email field of a form.

    Ensures that email address is not banned and that the xmpp server domain is not used.
    """
    error_messages = {
        'blacklist': _('This email address is banned from using this site.'),
    }

    def clean_email(self):
        email = self.cleaned_data['email']

        try:
            _node, domain = email.rsplit('@', 1)
        except ValueError:
            # Raised when the email address does not contain an '@'. This shouldn't happen to
            # normal users, because the form field already makes sure that it's a valid email
            # address.
            raise forms.ValidationError(_('Malformed email address.'))

        if domain in settings.XMPP_HOSTS \
                and not settings.XMPP_HOSTS[domain].get('ALLOW_EMAIL', False):

            raise forms.ValidationError(_(
                'Please give your own email address, %(domain)s does not provide one.')
                % {'domain': domain})

        # check if the address is in settings.EMAIL_BLACKLIST
        for regex in settings.EMAIL_BLACKLIST:
            if regex.search(email):
                raise forms.ValidationError(self.error_messages['blacklist'], code='blacklist')

        if settings.EMAIL_WHITELIST:
            matched = False
            for regex in settings.EMAIL_WHITELIST:
                if regex.search(email):
                    matched = True
                    break

            if matched is False:
                raise forms.ValidationError(_('Sorry, this email address cannot be used.'))

        return email


class AdminUserCreationForm(forms.ModelForm):
    username = UsernameAdminField()
    email = forms.EmailField(required=True, widget=AdminEmailInputWidget(),
                             help_text=_('A confirmation message will be sent to this address.'))

    class Meta:
        fields = ('username', 'email', )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.registration_method = REGISTRATION_MANUAL

        if commit:
            user.save()

        base_url = settings.XMPP_HOSTS[user.domain]['CANONICAL_BASE_URL']
        transaction.on_commit(lambda: send_confirmation_task.delay(
            user_pk=user.pk, purpose=PURPOSE_REGISTER, language='en', to=user.email,
            base_url=base_url, hostname=user.domain))
        return user


class AdminUserForm(forms.ModelForm):
    class Meta:
        widgets = {
            'default_language': forms.Select(choices=settings.LANGUAGES),
        }


class CreateUserForm(GPGMixin, BootstrapFormMixin, CaptchaFormMixin, EmailValidationMixin, forms.ModelForm):
    username = UsernameField(register=True)
    email = EmailVerifiedDomainField(
        label=_('Email'),
        help_text=_('Required, a confirmation email will be sent to this address.')
    )

    default_buttons = {
        'submit': {
            'text': _('Register'),
            'class': 'primary',
        },
    }

    def clean_email(self):
        email = super(CreateUserForm, self).clean_email()
        if settings.REQUIRE_UNIQUE_EMAIL and email and User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Email address is already used by another account.'))
        return email

    class Meta:
        model = User
        fields = ['username', 'email', 'gpg_fingerprint']


class LoginForm(BootstrapFormMixin, CaptchaFormMixin, AuthenticationForm):
    username = UsernameField()
    password = BootstrapPasswordField(label=_('Password'))

    default_buttons = {
        'submit': {
            'text': _('Login'),
            'class': 'primary',
        },
    }
    error_messages = {
        'invalid_login': _('Your username and password didn\'t match. Please try again.'),
    }


class NotificationsForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Notifications
        field_classes = {
            'account_expires': BootstrapBooleanField,
            'gpg_expires': BootstrapBooleanField,
        }
        fields = ['account_expires', 'gpg_expires', ]
        labels = {
            'account_expires': _('my account expires'),
            'gpg_expires': _('my GPG key expires'),
        }
        help_texts = {
            'account_expires': _(
                "Accounts are automatically removed if they haven't been used for a year."),
            'gpg_expires': _('If you have uploaded a GPG key and it is about to expire.'),
        }


class DeleteAccountForm(BootstrapFormMixin, forms.Form):
    password = BootstrapPasswordField(
        label=_('Password'), help_text=_(
            'Your password, to make sure that you really want to delete your account.'))

    default_buttons = {
        'submit': {
            'text': _('Delete account'),
            'class': 'primary',
        },
    }


class SetPasswordForm(BootstrapFormMixin, CaptchaFormMixin, SetPasswordFormBase):
    """Form used when the user can set his password *without* providing the old password.

    This is used for registration and password reset (users that forgot their password).
    """
    new_password1 = BootstrapSetPasswordField()
    new_password2 = BootstrapConfirmPasswordField()


class ConfirmRegistrationForm(SetPasswordForm):
    # override the button text
    default_buttons = {
        'submit': {
            'text': _('Complete registration'),
            'class': 'primary',
        },
    }


class ConfirmResetPasswordForm(SetPasswordForm):
    # override the button text
    default_buttons = {
        'submit': {
            'text': _('Reset password'),
            'class': 'primary',
        },
    }


class PasswordChangeForm(BootstrapFormMixin, PasswordChangeFormBase):
    """Form used when the user sets his password but has to provide his old password too.

    This is used for the "set password" functionality in the user-area of the homepage.
    """
    old_password = BootstrapPasswordField(
        label=_("Old password"), help_text=_('Your old password, just to be sure.'))
    new_password1 = BootstrapSetPasswordField(label=_('New password'))
    new_password2 = BootstrapConfirmPasswordField()

    default_buttons = {
        'submit': {
            'text': _('Set password'),
            'class': 'primary',
        },
    }


class SetEmailForm(GPGMixin, BootstrapFormMixin, EmailValidationMixin, forms.Form):
    email = EmailVerifiedDomainField(
        label=_('Email'),
        help_text=_('Required, an email will be sent to this address to confirm the change.')
    )

    default_buttons = {
        'submit': {
            'text': _('Set email'),
            'class': 'primary',
        },
    }


class AddGpgForm(GPGMixin, BootstrapFormMixin, forms.Form):
    hide_gpg_content = False

    def clean(self):
        data = super().clean()
        if not data.get('gpg_fingerprint') and not data.get('gpg_key'):
            error = forms.ValidationError(_('Please either upload a key or give a fingerprint.'),
                                          code='no-data')
            self.add_error(None, error)


class ResetPasswordForm(BootstrapFormMixin, CaptchaFormMixin, forms.Form):
    """Form used when a user forgot his password and forgot it."""

    username = UsernameField()

    default_buttons = {
        'submit': {
            'text': _('Request new password'),
            'class': 'primary',
        },
    }
