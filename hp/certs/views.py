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

from django.utils import timezone
from django.views.generic.detail import DetailView

#from .forms import SelectHostForm
from .models import Certificate


class CertificateView(DetailView):
    queryset = Certificate.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        now = timezone.now()
        queryset = queryset.filter(hostname=self.kwargs['hostname'])

        return queryset.filter(valid_until__gt=now, valid_from__lt=now).order_by('-created').first()
