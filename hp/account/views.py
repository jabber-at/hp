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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

#from django_xmpp_backends import backend

from .constants import PURPOSE_REGISTER
from .forms import CreateUserForm
from .models import UserConfirmation

User = get_user_model()


class RegisterUserView(CreateView):
    template_name_suffix = '_register'
    model = User
    form_class = CreateUserForm
    success_url = reverse_lazy('account:detail')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated() is True:
            return HttpResponseRedirect(reverse('account:detail'))
        return super(RegisterUserView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            response = super(RegisterUserView, self).form_valid(form)
            self.object.backend = settings.AUTHENTICATION_BACKENDS[0]

            confirmation = UserConfirmation.objects.create(user=self.object)
            kwargs = {
                'recipient': self.object.email,
            }
            kwargs.update(form.gpg_options(self.request))
            confirmation.send(self.request, self.object, PURPOSE_REGISTER, **kwargs)

            # TODO: only on confirmation
            #backend.create_user(self.object.node, self.object.domain, self.object.email)

            login(self.request, self.object)
            return response


class UserView(LoginRequiredMixin, TemplateView):
    template_name = 'account/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        context['object'] = self.request.user
        return context
