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

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.utils import translation

from celery import chain
from django_xmpp_backends import backend

from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_RESET_PASSWORD
from .forms import CreateUserForm
from .forms import LoginForm
from .forms import RequestPasswordResetForm
from .forms import SetPasswordForm
from .models import Confirmation
from .tasks import add_gpg_key_task
from .tasks import send_confirmation_task

User = get_user_model()
log = logging.getLogger(__name__)


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
        request = self.request
        address = request.META['REMOTE_ADDR']
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        with transaction.atomic():
            response = super(RegisterUserView, self).form_valid(form)
            user = self.object

            # log user creation, login
            with translation.override(lang):
                user.log(address=address, message=_('Account created.'))

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, user)

        task = send_confirmation_task.si(
            user_pk=user.pk, purpose=PURPOSE_REGISTER, language=lang,
            base_url=base_url, server=request.site['DOMAIN'])

        # Store GPG key if any
        fp, key = form.get_gpg_data(request)
        if fp or key:
            gpg_task = add_gpg_key_task.si(
                user_pk=user.pk, address=address, language=lang,
                fingerprint=fp, key=key)
            task = chain(gpg_task, task)
        task.delay()

        return response


class ConfirmRegistrationView(FormView):
    template_name = 'account/user_register_confirm.html'
    queryset = Confirmation.objects.select_related('user')
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

            # Actually create the user on the XMPP server
            backend.create_user(key.user.node, key.user.domain, key.user.email)

            # Delete the registration key
            key.delete()
        return super(ConfirmRegistrationView, self).form_valid(form)


class LoginView(FormView):
    """Class-based adaption of django.contrib.auth.views.login.

    We duplicate the functionality here because we want to redirect the user to the account
    detail page if already logged in. The default view always views the login form.
    """
    REDIRECT_FIELD_NAME = 'next'
    template_name = 'account/user_login.html'
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('account:detail'))
        return super(LoginView, self).dispatch(request, *args, **kwargs)


    def form_valid(self, form):
        redirect_to = self.request.POST.get(self.REDIRECT_FIELD_NAME, '')

        # Ensure the user-originating redirection url is safe.
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        # Okay, security check complete. Log the user in.
        login(self.request, form.get_user())
        return HttpResponseRedirect(redirect_to)

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context[self.REDIRECT_FIELD_NAME] = self.request.POST.get(
            self.REDIRECT_FIELD_NAME, self.request.GET.get(self.REDIRECT_FIELD_NAME, ''))
        return context


class RequestPasswordResetView(FormView):
    template_name = 'account/user_password_reset.html'
    form_class = RequestPasswordResetForm

    def form_valid(self, form):
        try:
            user = User.objects.filter(confirmed__isnull=False).get(
                username=form.cleaned_data['username'])
        except User.DoesNotExist:
            form.add_error('username', _('User not found.'))
            return self.form_invalid(form)

        confirmation = Confirmation.objects.create(user=user)
        kwargs = {
            'recipient': user.email,
        }
        kwargs.update(user.gpg_options(self.request))
        confirmation.send(self.request, user, PURPOSE_RESET_PASSWORD, **kwargs)

        return self.render_to_response(self.get_context_data(form=form))


class ResetPasswordView(FormView):
    template_name = 'account/user_password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('account:detail')
    queryset = Confirmation.objects.select_related('user')

    def form_valid(self, form):
        with transaction.atomic():
            key = self.queryset.get(key=self.kwargs['key'])
            backend.set_password(username=key.user.node, domain=key.user.domain,
                                 password=form.cleaned_data['password'])

            key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, key.user)
            key.delete()
        return super(ResetPasswordView, self).form_valid(form)

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
        if User.objects.filter(username=jid).exists():
            cache.set(cache_key, True, 30)
            return HttpResponse('', status=409)
        else:
            cache.set(cache_key, False, 30)
            return HttpResponse('')
