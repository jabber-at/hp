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

from django.conf import settings
from django.contrib.auth import login
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView

from django_xmpp_backends import backend

from .forms import CreateUserForm
from .models import User


class CreateUserView(CreateView):
    template_name = 'account/user_register.html'
    model = User
    form_class = CreateUserForm
    success_url = reverse_lazy('account:detail')

    def form_valid(self, form):
        with transaction.atomic():
            response = super(CreateUserView, self).form_valid(form)
            self.object.backend = settings.AUTHENTICATION_BACKENDS[0]

            backend.create_user(self.object.node, self.object.domain, self.object.email)
            login(self.request, self.object)
            return response


class UserView(DetailView):
    model = User

    def get_object(self, *args, **kwargs):
        return self.request.user
