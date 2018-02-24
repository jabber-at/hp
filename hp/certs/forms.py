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
