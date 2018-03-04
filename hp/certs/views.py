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
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .forms import SelectCertificateForm
from .models import Certificate


class CertificateOverview(ListView):
    """List all available hostnames and the last update."""

    queryset = Certificate.objects.enabled()
    template_name = 'certs/certificate_list.html'

    def get_queryset(self):
        qs = super(CertificateOverview, self).get_queryset()
        certs = []

        for hostname in settings.XMPP_HOSTS.keys():
            # first we get the newest valid one
            cert = qs.hostname(hostname).valid().first()

            if cert:
                certs.append(cert)

        return certs


class CertificateView(FormView):
    context_object_name = 'cert'
    form_class = SelectCertificateForm
    template_name = 'certs/certificate_detail.html'

    def get_certificate(self, current):

        if 'date' not in self.kwargs:
            return current

        queryset = Certificate.objects.enabled().hostname(self.hostname)
        obj = queryset.filter(valid_from__date=self.kwargs['date']).first()

        if obj is None:
            raise Http404
        return obj

    def get_current_certificate(self):
        """Returns the currently used certificate, meaning the last one issued."""

        return Certificate.objects.enabled().hostname(self.hostname).order_by('-valid_from').first()

    def dispatch(self, request, *args, **kwargs):
        self.hostname = self.kwargs['hostname']
        self.current_certificate = self.get_current_certificate()
        self.certificate = self.get_certificate(self.current_certificate)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['hostname'] = self.kwargs['hostname']
        return kwargs

    def get_initial(self):
        return {
            'certificate': self.certificate,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hostname'] = self.hostname
        context['cert'] = self.certificate
        context['current_cert'] = self.current_certificate
        context['is_current'] = self.certificate == self.current_certificate
        context['cert_id'] = 'date' in self.kwargs
        return context

    def form_valid(self, form):
        cert = form.cleaned_data['certificate']
        url = reverse('certs:cert-id', kwargs={'hostname': self.hostname, 'date': cert.valid_from})
        return HttpResponseRedirect(url)
