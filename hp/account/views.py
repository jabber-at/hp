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

from django.db import transaction
from django.views.generic.edit import CreateView

from django_xmpp_backends import backend

from .forms import CreateUserForm
from .models import User


class CreateUserView(CreateView):
    template_name = 'account/user_register.html'
    model = User
    form_class = CreateUserForm

    def form_valid(self, form):
        with transaction.atomic():
            user = form.instance
            backend.create_user(user.node, user.domain, user.email)
            return super(CreateUserView, self).form_valid(form)
