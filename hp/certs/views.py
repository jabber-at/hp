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

from django.conf import settings
from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .forms import SelectCertificateForm
from .models import Certificate


class CertificateOverview(ListView):
    """List all available hostnames and the last update."""

    queryset = Certificate.objects.all()
    template_name = 'certs/certificate_list.html'

    def get_queryset(self):
        qs = super(CertificateOverview, self).get_queryset()
        certs = []

        for hostname in settings.XMPP_HOSTS.keys():
            # first we get the newest valid one
            cert = qs.filter(hostname=hostname).valid().first()

            if cert:
                certs.append(cert)

        return certs


class CertificateView(DetailView):
    context_object_name = 'cert'
    queryset = Certificate.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        queryset = queryset.filter(hostname=self.kwargs['hostname'])

        if 'date' in self.kwargs:
            queryset = queryset.filter(valid_from__date=self.kwargs['date'])
        else:
            queryset = queryset.order_by('-valid_from')

        obj = queryset.first()
        if obj is None:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hostname = self.kwargs['hostname']
        context['all_certs'] = Certificate.objects.filter(hostname=hostname)
        context['form'] = SelectCertificateForm(hostname=hostname)
        return context
