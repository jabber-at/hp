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

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from django import forms
from django.conf import settings
from django.utils.formats import date_format

from bootstrap.formfields import BootstrapModelChoiceField

from .models import Certificate


class CertificateSelectionField(BootstrapModelChoiceField):
    def label_from_instance(self, obj):
        return '%s - %s' % (
            date_format(obj.valid_from, format='SHORT_DATE_FORMAT', use_l10n=True),
            date_format(obj.valid_until, format='SHORT_DATE_FORMAT', use_l10n=True)
        )


class CertificateAdminForm(forms.ModelForm):
    hostname = forms.ChoiceField(choices=[(k, k) for k in settings.XMPP_HOSTS])

    def clean_pem(self):
        pem = self.cleaned_data['pem']

        try:
            backend = default_backend()
            x509.load_pem_x509_certificate(pem.encode(), backend)
        except Exception as e:
            raise forms.ValidationError('%s: %s' % (type(e).__name__, e))

        return pem


class SelectCertificateForm(forms.Form):
    certificate = CertificateSelectionField(queryset=None, required=True, empty_label=None,
                                            hide_label=True, input_cols=4)

    def __init__(self, *args, **kwargs):
        hostname = kwargs.pop('hostname', settings.DEFAULT_XMPP_HOST)
        super().__init__(*args, **kwargs)
        self.fields['certificate'].queryset = Certificate.objects.filter(hostname=hostname)
