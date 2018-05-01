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

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from bootstrap.formfields import BootstrapCharField
from bootstrap.formfields import BootstrapEmailField
from bootstrap.formfields import BootstrapTextField

from .formfields import CaptchaField
from .modelfields import LinkTargetDict


class MenuItemAdminForm(forms.ModelForm):
    def clean_target(self):
        target = LinkTargetDict(self.cleaned_data['target'])
        target.validate()
        return target


class CaptchaFormMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # NOTE: Add conditional field in constructor and not in class definition, this way Django test cases
        #       work with enabling/disabling CAPTCHASwith override_settings.
        if settings.ENABLE_CAPTCHAS:
            self.fields['captcha'] = CaptchaField(help_text=_(
                'This <a href="https://en.wikipedia.org/wiki/CAPTCHA">CAPTCHA</a> prevents '
                'automated SPAM. If you can\'t read it, just <a '
                'class="captcha-refresh">&#8634; reload</a> it.'
            ))


class ContactForm(forms.Form):
    subject = BootstrapCharField(min_length=12, max_length=30, help_text=_(
        'At least 12, at most 30 characters. What is you message about?'))
    text = BootstrapTextField(min_length=100, help_text=_(
        'Please describe your issue as detailed as possible!'))

    def clean_text(self):
        text = self.cleaned_data['text']
        if re.findall('https?://', text):
            raise forms.ValidationError(_('Sorry, you cannot use links in the contact form.'))
        return text


class AnonymousContactForm(CaptchaFormMixin, ContactForm):
    email = BootstrapEmailField(help_text=_('Your address, so we can get back to you.'))
