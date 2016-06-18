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
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.core.cache import cache

from django_xmpp_backends import backend

from .constants import PURPOSE_REGISTER
from .forms import CreateUserForm
from .forms import SetPasswordForm
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

            login(self.request, self.object)
            return response


class ConfirmRegistrationView(FormView):
    template_name = 'account/user_register_confirm.html'
    queryset = UserConfirmation.objects.select_related('user')
    form_class = SetPasswordForm
    success_url = reverse_lazy('account:detail')

    def form_valid(self, form):
        with transaction.atomic():
            key = self.queryset.get(key=self.kwargs['key'])
            key.user.confirmed = timezone.now()
            key.user.save()

            if key.user.is_authenticated() is False:
                key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(self.request, key.user)

            backend.create_user(key.user.node, key.user.domain, key.user.email)
            key.delete()
        return super(ConfirmRegistrationView, self).form_valid(form)


class UserView(LoginRequiredMixin, TemplateView):
    template_name = 'account/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserView, self).get_context_data(**kwargs)
        context['object'] = self.request.user
        return context


class UserAvailableView(View):
    def post(self, request):
        # Note: XMPP usernames are case insensitive
        username = request.POST.get('username', '').strip().lower()
        domain = request.POST.get('domain', '').strip().lower()
        jid = '%s@%s' % (username, domain)

        cache_key = 'exists_%s' % jid
        exists = cache.get(cache_key)
        if exists is True:
            return HttpResponse('', status=409)
        elif exists is False:
            return HttpResponse('')

        # Check if the user exists in the database
        if User.objects.filter(jid=jid).exists():
            cache.set(cache_key, True, 30)
            return HttpResponse('', status=409)

        # TODO: Add a setting to rely on the contents of the database and not ask the backend.

        # Check if the user exists in the backend
        if backend.user_exists(username, domain):
            cache.set(cache_key, True, 30)
            return HttpResponse('', status=409)
        else:
            cache.set(cache_key, False, 30)
            return HttpResponse('')
