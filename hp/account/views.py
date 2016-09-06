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
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView

from celery import chain
from django_xmpp_backends import backend

from core.constants import ACTIVITY_REGISTER
from core.constants import ACTIVITY_RESET_PASSWORD
from core.constants import ACTIVITY_SET_EMAIL
from core.constants import ACTIVITY_SET_PASSWORD
from core.constants import ACTIVITY_FAILED_LOGIN
from core.models import AddressActivity
from core.views import AnonymousRequiredMixin
from core.views import DnsBlMixin
from core.views import RateLimitMixin

from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_SET_EMAIL
from .forms import CreateUserForm
from .forms import LoginForm
from .forms import RequestPasswordResetForm
from .forms import SetEmailForm
from .forms import SetPasswordForm
from .forms import ResetPasswordForm
from .models import Confirmation
from .tasks import add_gpg_key_task
from .tasks import send_confirmation_task
from .tasks import set_email_task

User = get_user_model()
log = logging.getLogger(__name__)


class AccountPageMixin(object):
    """Mixin that adds the usermenu on the left to views where the user is logged in."""

    usermenu = (
        ('account:detail', _('Overview'), False),
        ('account:set_password', _('Set password'), True),
        ('account:set_email', _('Set E-Mail'), True),
        ('account:gpg', _('GPG keys'), True),
        ('account:log', _('Recent activity'), False),
    )
    usermenu_item = None
    requires_confirmation = True

    def dispatch(self, request, *args, **kwargs):
        if self.requires_confirmation and not request.user.created_in_backend:
            context = self.get_context_data()
            return TemplateResponse(request, 'account/requires_confirmation.html', context)

        return super(AccountPageMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccountPageMixin, self).get_context_data(**kwargs)

        usermenu = []
        for urlname, title, requires_confirmation in self.usermenu:
            if self.request.user.created_in_backend is False and requires_confirmation is True:
                continue

            usermenu.append({
                'path': reverse(urlname),
                'title': title,
                'active': ' active' if urlname == self.usermenu_item else '',
            })
        context['usermenu'] = usermenu

        return context


class UserDetailView(DetailView):
    """Custom detail view to use the current user."""

    def get_object(self):
        return self.request.user


class RegisterUserView(DnsBlMixin, RateLimitMixin, AnonymousRequiredMixin, CreateView):
    template_name_suffix = '_register'
    model = User
    form_class = CreateUserForm
    success_url = reverse_lazy('account:detail')
    rate_activity = ACTIVITY_REGISTER

    def form_valid(self, form):
        request = self.request
        self.ratelimit(request)
        address = request.META['REMOTE_ADDR']
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        with transaction.atomic():
            response = super(RegisterUserView, self).form_valid(form)
            user = self.object

            # log user creation, display help message.
            user.log(address=address, message=_('Account created.'))
            AddressActivity.objects.log(request, ACTIVITY_REGISTER, user=user)

            messages.success(request, _(
                """Successfully created the account %s. A confirmation email was just sent to the
email address you provided (%s). Before you can use your account, you must click on the
confirmation link in that email.""" % (user.username, user.email)))

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, user)

        task = send_confirmation_task.si(
            user_pk=user.pk, purpose=PURPOSE_REGISTER, language=lang, to=user.email,
            base_url=base_url, server=request.site['DOMAIN'])

        # Store GPG key if any
        fp, key = form.get_gpg_data()
        if fp or key:
            gpg_task = add_gpg_key_task.si(
                user_pk=user.pk, address=address, language=lang,
                fingerprint=fp, key=key)
            task = chain(gpg_task, task)
        task.delay()

        return response


class ConfirmRegistrationView(FormView):
    """View for confirming a registration e-mail."""

    template_name = 'account/user_register_confirm.html'
    queryset = Confirmation.objects.valid().purpose(
        PURPOSE_REGISTER).select_related('user')
    form_class = ResetPasswordForm
    success_url = reverse_lazy('account:detail')

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']
        password = form.cleaned_data['password']

        with transaction.atomic():
            key = self.queryset.get(key=self.kwargs['key'])
            key.user.confirmed = timezone.now()
            key.user.save()

            if key.user.is_authenticated() is False:
                key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, key.user)

            # Actually create the user on the XMPP server
            backend.create_user(username=key.user.node, domain=key.user.domain, password=password,
                                email=key.user.email)

            key.user.log(_('Email address %(email)s confirmed.') % {
                'email': key.user.email
            }, address)
            # TODO: More meaningful help message on a webchat, usable clients, follow updates, ...
            messages.success(request, _(
                "Successfully confirmed your email address. You can now use your account."))

            # Delete the registration key
            key.delete()

        return super(ConfirmRegistrationView, self).form_valid(form)


class LoginView(DnsBlMixin, RateLimitMixin, AnonymousRequiredMixin, FormView):
    """Class-based adaption of django.contrib.auth.views.login.

    We duplicate the functionality here because we want to redirect the user to the account
    detail page if already logged in. The default view always views the login form.
    """
    REDIRECT_FIELD_NAME = 'next'
    template_name = 'account/user_login.html'
    form_class = LoginForm
    rate_activity = ACTIVITY_FAILED_LOGIN

    def form_valid(self, form):
        redirect_to = self.request.POST.get(self.REDIRECT_FIELD_NAME, '')

        # Ensure the user-originating redirection url is safe.
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        # Okay, security check complete. Log the user in.
        login(self.request, form.get_user())
        return HttpResponseRedirect(redirect_to)

    def form_invalid(self, form):
        self.ratelimit(self.request)
        return super(LoginView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context[self.REDIRECT_FIELD_NAME] = self.request.POST.get(
            self.REDIRECT_FIELD_NAME, self.request.GET.get(self.REDIRECT_FIELD_NAME, ''))
        return context


class RequestPasswordResetView(DnsBlMixin, AnonymousRequiredMixin, FormView):
    template_name = 'account/user_password_reset.html'
    form_class = RequestPasswordResetForm

    def form_valid(self, form):
        try:
            user = User.objects.filter(confirmed__isnull=False).get(
                username=form.cleaned_data['username'])
        except User.DoesNotExist:
            form.add_error('username', _('User not found.'))
            return self.form_invalid(form)

        request = self.request
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        user.log(_('Requested password reset.'), request.META['REMOTE_ADDR'])
        AddressActivity.objects.log(request, ACTIVITY_RESET_PASSWORD, user=user)

        send_confirmation_task.delay(
            user_pk=user.pk, purpose=PURPOSE_RESET_PASSWORD, language=lang, to=user.email,
            base_url=base_url, server=request.site['DOMAIN'])

        return self.render_to_response(self.get_context_data(form=form))


class ResetPasswordView(FormView):
    template_name = 'account/user_password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('account:detail')
    queryset = Confirmation.objects.select_related('user')

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']

        with transaction.atomic():
            key = self.queryset.get(key=self.kwargs['key'])
            backend.set_password(username=key.user.node, domain=key.user.domain,
                                 password=form.cleaned_data['password'])

            key.user.log(_('Set new password.'), address)
            messages.success(request, _('Successfully changed your password.'))

            key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, key.user)
            key.delete()

        return super(ResetPasswordView, self).form_valid(form)


class SetPasswordView(LoginRequiredMixin, AccountPageMixin, FormView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('account:detail')
    template_name = 'account/set_password.html'
    usermenu_item = 'account:set_password'

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']
        user = request.user
        password = form.cleaned_data['password']

        backend.set_password(username=user.node, domain=user.domain, password=password)
        user.log(_('Set new password.'), address)
        AddressActivity.objects.log(request, ACTIVITY_SET_PASSWORD)
        messages.success(request, _('Successfully changed your password.'))
        return super(SetPasswordView, self).form_valid(form)


class SetEmailView(LoginRequiredMixin, AccountPageMixin, FormView):
    success_url = reverse_lazy('account:detail')
    usermenu_item = 'account:set_email'
    template_name = 'account/user_set_email.html'
    form_class = SetEmailForm

    def form_valid(self, form):
        request = self.request
        user = request.user
        address = request.META['REMOTE_ADDR']

        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())
        to = form.cleaned_data['email']

        fp, key = form.get_gpg_data()
        set_email_task.delay(
            user_pk=user.pk, to=to, address=address, language=lang, fingerprint=fp, key=key,
            base_url=base_url, server=request.site['DOMAIN'])

        messages.success(request, _(
            'We sent you an email to your new email address (%s). Click on the link in it to '
            'confirm it.') % to)
        user.log(_('Requested change of email address to %s.') % to, address=address)
        AddressActivity.objects.log(request, ACTIVITY_SET_EMAIL, note=to)

        return super(SetEmailView, self).form_valid(form)


class ConfirmSetEmailView(LoginRequiredMixin, RedirectView):
    """Confirmation view for a user setting his email address, redirects to account detail page."""

    pattern_name = 'account:detail'  # where to redirect to
    queryset = Confirmation.objects.valid().purpose(PURPOSE_SET_EMAIL)

    def get_redirect_url(self, *args, **kwargs):
        request = self.request
        user = request.user
        qs = self.queryset.filter(user=user)
        key = get_object_or_404(qs, key=kwargs['key'])

        user.email = key.to
        user.confirmed = timezone.now()

        with transaction.atomic():
            # Update list of GPG keys
            user.gpg_keys.all().delete()
            gpg_keys = key.payload.get('gpg_key')
            if gpg_keys:
                add_gpg_key_task.delay(user_pk=user.pk, address=key.payload['address'],
                                       language=request.LANGUAGE_CODE, key=gpg_keys)

            user.save()
            key.delete()

            messages.success(request, _('Changed email address to %s.') % user.email)
            user.log(_('Confirmed email address change to %s.') % key.to,
                     self.request.META['REMOTE_ADDR'])

            return super(ConfirmSetEmailView, self).get_redirect_url()


class UserView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:detail'
    requires_confirmation = False


class GpgView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:gpg'
    template_name = 'account/user_gpg.html'


class RecentActivityView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:log'
    template_name = 'account/user_recent_activity.html'
    requires_confirmation = False

    def get_context_data(self, **kwargs):
        context = super(RecentActivityView, self).get_context_data(**kwargs)
        context['logentry_expires'] = settings.USER_LOGENTRY_EXPIRES
        return context


class UserAvailableView(View):
    """Ajax view to check if a username is still available (used during registration)."""

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
