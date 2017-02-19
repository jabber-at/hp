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
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView

from celery import chain
from xmpp_http_upload.models import Upload
from xmpp_backends.django import xmpp_backend

from core.constants import ACTIVITY_REGISTER
from core.constants import ACTIVITY_RESET_PASSWORD
from core.constants import ACTIVITY_SET_EMAIL
from core.constants import ACTIVITY_SET_PASSWORD
from core.constants import ACTIVITY_FAILED_LOGIN
from core.models import AddressActivity
from core.views import AnonymousRequiredMixin
from core.views import AntiSpamMixin
from core.views import StaticContextMixin

from .constants import PURPOSE_DELETE
from .constants import PURPOSE_REGISTER
from .constants import PURPOSE_RESET_PASSWORD
from .constants import PURPOSE_SET_EMAIL
from .forms import CreateUserForm
from .forms import LoginForm
from .forms import ConfirmResetPasswordForm
from .forms import DeleteAccountForm
from .forms import NotificationsForm
from .forms import SetEmailForm
from .forms import SetPasswordForm
from .forms import ResetPasswordForm
from .forms import AddGpgForm
from .models import Confirmation
from .tasks import add_gpg_key_task
from .tasks import send_confirmation_task
from .tasks import set_email_task

User = get_user_model()
log = logging.getLogger(__name__)
_confirmation_qs = Confirmation.objects.valid().select_related('user')


class AccountPageMixin(StaticContextMixin):
    """Mixin that adds the usermenu on the left to views where the user is logged in."""

    usermenu = (
        ('account:detail', _('Overview'), False),
        ('account:notifications', _('Notifications'), True),
        ('account:set_password', _('Set password'), True),
        ('account:set_email', _('Set E-Mail'), True),
        ('account:xep0363', _('HTTP uploads'), True),
        ('account:gpg', _('GPG keys'), True),
        ('account:log', _('Recent activity'), False),
        ('account:delete', _('Delete account'), True),
    )
    usermenu_item = None
    requires_email = False
    requires_confirmation = True

    def dispatch(self, request, *args, **kwargs):
        if self.requires_confirmation and not request.user.created_in_backend:
            kwargs = {}
            if isinstance(self, SingleObjectMixin):
                self.object = self.get_object()
                kwargs['object'] = self.object
            context = self.get_context_data(**kwargs)

            return TemplateResponse(request, 'account/requires_confirmation.html', context)
        elif self.requires_email and not request.user.email:
            kwargs = {}
            if isinstance(self, SingleObjectMixin):
                self.object = self.get_object()
                kwargs['object'] = self.object
            context = self.get_context_data(**kwargs)

            return TemplateResponse(request, 'account/requires_email.html', context)

        return super(AccountPageMixin, self).dispatch(request, *args, **kwargs)

    def get_usermenu(self):
        usermenu = []
        for urlname, config in settings.ACCOUNT_USER_MENU:
            req_confirmation = config.get('requires_confirmation', True)
            if self.request.user.created_in_backend is False and req_confirmation is True:
                continue

            usermenu.append({
                'path': reverse(urlname),
                'title': config.get('title', 'No title'),
                'active': ' active' if urlname == self.usermenu_item else '',
            })
        return usermenu

    def get_context_data(self, **kwargs):
        context = super(AccountPageMixin, self).get_context_data(**kwargs)
        context['usermenu'] = self.get_usermenu()
        return context


class UserObjectMixin(object):
    """Mixin that returns the current user as object for views using SingleObjectMixin."""

    def get_object(self):
        return self.request.user


class RegistrationView(AntiSpamMixin, AnonymousRequiredMixin, StaticContextMixin, CreateView):
    form_class = CreateUserForm
    model = User
    rate_activity = ACTIVITY_REGISTER
    success_url = reverse_lazy('account:detail')
    template_name_suffix = '_register'

    def form_valid(self, form):
        request = self.request
        self.ratelimit(request)
        address = request.META['REMOTE_ADDR']
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        with transaction.atomic():
            response = super(RegistrationView, self).form_valid(form)
            user = self.object

            # save default language
            user.default_language = lang
            user.save()

            # log user creation, display help message.
            user.log(ugettext_noop('Account created.'), address=address)
            AddressActivity.objects.log(request, ACTIVITY_REGISTER, user=user, note=user.email)

            messages.success(request, _(
                """Successfully created the account %(username)s. A confirmation email was
just sent to the email address you provided (%(email)s). Before you can use
your account, you must click on the confirmation link in that email.""") % {
                    'username': user.username,
                    'email': user.email,
            })

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, user)

        task = send_confirmation_task.si(
            user_pk=user.pk, purpose=PURPOSE_REGISTER, language=lang, address=address,
            to=user.email, base_url=base_url, hostname=request.site['NAME'])

        # Store GPG key if any
        fp, key = form.get_gpg_data()
        if fp or key:
            gpg_task = add_gpg_key_task.si(
                user_pk=user.pk, address=address, fingerprint=fp, key=key)
            task = chain(gpg_task, task)
        task.delay()

        return response


class ConfirmationMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            self.key = self.queryset.get(key=self.kwargs['key'])
        except Confirmation.DoesNotExist:
            # We set None here because we only want to show a 404 when the user actually submits a
            # form. This is a minor protection against guessing attacks.
            self.key = None

        return super(ConfirmationMixin, self).dispatch(request, *args, **kwargs)

    def get_key(self):
        if self.key is None:
            name, ext = os.path.splitext(self.template_name)
            template = '%s_not_found%s' % (name, ext)
            return TemplateResponse(self.request, template, {}, status=404)
        return self.key


class ConfirmRegistrationView(ConfirmationMixin, FormView):
    """View for confirming a registration e-mail."""

    form_class = ConfirmResetPasswordForm
    queryset = _confirmation_qs.purpose(PURPOSE_REGISTER)
    success_url = reverse_lazy('account:detail')
    template_name = 'account/user_register_confirm.html'

    def get_form_kwargs(self):
        kwargs = super(ConfirmRegistrationView, self).get_form_kwargs()
        if self.key is not None:
            kwargs['instance'] = self.key.user
        return kwargs

    def form_valid(self, form):
        key = self.get_key()
        if isinstance(key, HttpResponse):
            return key

        request = self.request
        address = request.META['REMOTE_ADDR']
        password = form.cleaned_data['password']

        with transaction.atomic():
            key.user.confirmed = timezone.now()
            key.user.created_in_backend = True
            key.user.save()

            if request.user != key.user:
                logout(request)  # logout any previous user
                key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, key.user)

            # Actually create the user on the XMPP server
            xmpp_backend.create_user(username=key.user.node, domain=key.user.domain,
                                     password=password, email=key.user.email)

            key.user.log(ugettext_noop('Email address %(email)s confirmed.'), address,
                         email=key.user.email)
            # TODO: More meaningful help message on a webchat, usable clients, follow updates, ...
            messages.success(request, _(
                "Successfully confirmed your email address. You can now use your account."))

            # Delete the registration key
            key.delete()

        return super(ConfirmRegistrationView, self).form_valid(form)


class LoginView(AntiSpamMixin, AnonymousRequiredMixin, FormView):
    """Class-based adaption of django.contrib.auth.views.login.

    We duplicate the functionality here because we want to redirect the user to the account
    detail page if already logged in. The default view always views the login form.
    """
    REDIRECT_FIELD_NAME = 'next'
    form_class = LoginForm
    rate_activity = ACTIVITY_FAILED_LOGIN
    template_name = 'account/user_login.html'

    def form_valid(self, form):
        redirect_to = self.request.POST.get(self.REDIRECT_FIELD_NAME, '')

        # Ensure the user-originating redirection url is safe.
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

        user = form.get_user()
        now = timezone.now()

        # Okay, security check complete. Log the user in.
        login(self.request, user)
        user.last_activity = now
        xmpp_backend.set_last_activity(user.node, user.domain,
                                       status='Logged in via homepage.',
                                       timestamp=now)
        user.save()
        return HttpResponseRedirect(redirect_to)

    def form_invalid(self, form):
        self.ratelimit(self.request)
        return super(LoginView, self).form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(LoginView, self).get_context_data(**kwargs)
        context[self.REDIRECT_FIELD_NAME] = self.request.POST.get(
            self.REDIRECT_FIELD_NAME, self.request.GET.get(self.REDIRECT_FIELD_NAME, ''))
        return context


class UserView(LoginRequiredMixin, AccountPageMixin, UserObjectMixin, DetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:detail'
    requires_confirmation = False


class ResetPasswordView(AntiSpamMixin, AnonymousRequiredMixin, FormView):
    form_class = ResetPasswordForm
    rate_activity = ACTIVITY_RESET_PASSWORD
    template_name = 'account/user_password_reset.html'

    def form_valid(self, form):
        self.ratelimit(self.request)

        try:
            user = User.objects.filter(confirmed__isnull=False).get(
                username=form.cleaned_data['username'])
        except User.DoesNotExist:
            form.add_error('username', _('User not found.'))
            return self.form_invalid(form)

        request = self.request
        address = request.META['REMOTE_ADDR']
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        user.log(ugettext_noop('Requested password reset.'), address)
        AddressActivity.objects.log(request, ACTIVITY_RESET_PASSWORD, user=user)

        send_confirmation_task.delay(
            user_pk=user.pk, purpose=PURPOSE_RESET_PASSWORD, language=lang, address=address,
            to=user.email, base_url=base_url, hostname=request.site['NAME'])

        return self.render_to_response(self.get_context_data(form=form))


class ConfirmResetPasswordView(ConfirmationMixin, FormView):
    form_class = ConfirmResetPasswordForm
    queryset = _confirmation_qs.purpose(PURPOSE_RESET_PASSWORD)
    success_url = reverse_lazy('account:detail')
    template_name = 'account/user_password_reset_confirm.html'

    def form_valid(self, form):
        key = self.get_key()
        if isinstance(key, HttpResponse):
            return key

        request = self.request
        address = request.META['REMOTE_ADDR']

        with transaction.atomic():
            xmpp_backend.set_password(username=key.user.node, domain=key.user.domain,
                                      password=form.cleaned_data['password'])

            key.user.log(ugettext_noop('Set new password.'), address)
            messages.success(request, _('Successfully changed your password.'))

            key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, key.user)
            key.delete()

        return super(ConfirmResetPasswordView, self).form_valid(form)


class SessionsView(LoginRequiredMixin, AccountPageMixin, TemplateView):
    template_name = 'account/sessions.html'
    usermenu_item = 'account:sessions'

    def get_context_data(self, **kwargs):
        context = super(SessionsView, self).get_context_data(**kwargs)
        user = self.request.user
        context['sessions'] = xmpp_backend.user_sessions(user.node, user.domain)
        return context


class NotificationsView(LoginRequiredMixin, AccountPageMixin, UpdateView):
    form_class = NotificationsForm
    requires_email = True
    template_name = 'account/notifications.html'
    usermenu_item = 'account:notifications'

    def get_object(self):
        return self.request.user.notifications

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponse('Ok.')


class SetPasswordView(LoginRequiredMixin, AccountPageMixin, FormView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('account:detail')
    template_name = 'account/set_password.html'
    usermenu_item = 'account:set_password'

    def get_form_kwargs(self):
        kwargs = super(SetPasswordView, self).get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']
        user = request.user
        password = form.cleaned_data['password']

        xmpp_backend.set_password(username=user.node, domain=user.domain, password=password)
        user.log(ugettext_noop('Set new password.'), address)
        AddressActivity.objects.log(request, ACTIVITY_SET_PASSWORD)
        messages.success(request, _('Successfully changed your password.'))
        return super(SetPasswordView, self).form_valid(form)


class SetEmailView(LoginRequiredMixin, AccountPageMixin, FormView):
    form_class = SetEmailForm
    success_url = reverse_lazy('account:detail')
    template_name = 'account/user_set_email.html'
    usermenu_item = 'account:set_email'

    def form_valid(self, form):
        request = self.request
        user = request.user
        address = request.META['REMOTE_ADDR']
        to = form.cleaned_data['email']

        # If REQUIRE_UNIQUE_EMAIL is true, validate uniquenss

        qs = User.objects.exclude(pk=user.pk).filter(email=to)
        if settings.REQUIRE_UNIQUE_EMAIL and qs.exists():
            form.add_error('email', _('Email address is already used by another account.'))
            return self.form_invalid(form)

        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        fp, key = form.get_gpg_data()
        set_email_task.delay(
            user_pk=user.pk, to=to, language=lang, address=address, fingerprint=fp, key=key,
            base_url=base_url, hostname=request.site['NAME'])

        messages.success(request, _(
            'We sent you an email to your new email address (%(email)s). Click on the link in it '
            'to confirm it.') % {'email': to})
        user.log(ugettext_noop('Requested change of email address to %(email)s.'), address,
                 email=to)
        AddressActivity.objects.log(request, ACTIVITY_SET_EMAIL, note=to)

        return super(SetEmailView, self).form_valid(form)


class ConfirmSetEmailView(LoginRequiredMixin, RedirectView):
    """Confirmation view for a user setting his email address, redirects to account detail page."""

    pattern_name = 'account:detail'  # where to redirect to
    queryset = _confirmation_qs.purpose(PURPOSE_SET_EMAIL)

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
            gpg_keys = key.payload.get('gpg_recv_pub')
            if gpg_keys:
                add_gpg_key_task.delay(user_pk=user.pk, address=key.address.address, key=gpg_keys)

            user.save()
            key.delete()

            messages.success(request,
                             _('Confirmed email address change to %(email)s.')
                             % {'email': user.email, })
            user.log(ugettext_noop('Confirmed email address change to %(email)s.'),
                     request.META['REMOTE_ADDR'], email=key.to)

            return super(ConfirmSetEmailView, self).get_redirect_url()


class HttpUploadView(LoginRequiredMixin, AccountPageMixin, UserObjectMixin, DetailView):
    usermenu_item = 'account:xep0363'
    template_name = 'account/xep0363.html'

    def get_context_data(self, **kwargs):
        context = super(HttpUploadView, self).get_context_data(**kwargs)
        context['uploads'] = Upload.objects.filter(jid=context['object'].username)
        return context


class GpgView(LoginRequiredMixin, AccountPageMixin, UserObjectMixin, DetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:gpg'
    template_name = 'account/user_gpg.html'


class AddGpgView(LoginRequiredMixin, AccountPageMixin, FormView):
    form_class = AddGpgForm
    success_url = reverse_lazy('account:gpg')
    template_name = 'account/add_gpg.html'
    usermenu_item = 'account:gpg'

    def form_valid(self, form):
        request = self.request
        user = request.user
        address = request.META['REMOTE_ADDR']

        fp, key = form.get_gpg_data()
        add_gpg_key_task.delay(user_pk=user.pk, address=address, fingerprint=fp, key=key)

        messages.success(request, _('Processing new GPG key, it will be added in a moment.'))

        return super(AddGpgView, self).form_valid(form)


class RecentActivityView(LoginRequiredMixin, AccountPageMixin, UserObjectMixin, DetailView):
    """Main user settings view (/account)."""

    requires_confirmation = False
    template_name = 'account/user_recent_activity.html'
    usermenu_item = 'account:log'

    def get_context_data(self, **kwargs):
        context = super(RecentActivityView, self).get_context_data(**kwargs)
        context['logentry_expires'] = settings.USER_LOGENTRY_EXPIRES
        return context


class DeleteAccountView(LoginRequiredMixin, AccountPageMixin, FormView):
    usermenu_item = 'account:delete'
    form_class = DeleteAccountForm
    template_name = 'account/delete.html'
    requires_email = True

    def form_valid(self, form):
        password = form.cleaned_data['password']
        request = self.request
        user = request.user

        if not xmpp_backend.check_password(user.node, user.domain, password=password):
            form.add_error('password', _('The password is incorrect.'))
            return self.form_invalid(form)

        address = request.META['REMOTE_ADDR']
        lang = request.LANGUAGE_CODE
        base_url = '%s://%s' % (request.scheme, request.get_host())

        send_confirmation_task.delay(
            user_pk=user.pk, purpose=PURPOSE_DELETE, language=lang, address=address,
            to=user.email, base_url=base_url, hostname=request.site['NAME'])

        messages.success(request, _(
            'We sent you an email to %(email)s to confirm your request.') %
            {'email': user.email, })
        user.log(ugettext_noop('Requested deletion of account.'), address)
        AddressActivity.objects.log(request, ACTIVITY_SET_EMAIL, note=user.email)

        return HttpResponseRedirect(reverse('account:detail'))


class ConfirmDeleteAccountView(LoginRequiredMixin, AccountPageMixin, FormView):
    usermenu_item = 'account:delete'
    form_class = DeleteAccountForm
    template_name = 'account/delete_confirm.html'
    queryset = _confirmation_qs.purpose(PURPOSE_DELETE)

    def form_valid(self, form):
        password = form.cleaned_data['password']
        request = self.request
        user = request.user

        # Check the password of the user again
        if not xmpp_backend.check_password(user.node, user.domain, password=password):
            form.add_error('password', _('The password is incorrect.'))
            return self.form_invalid(form)

        # Verify the confirmation key
        key = get_object_or_404(self.queryset.filter(user=user), key=self.kwargs['key'])

        # Log the user out, delete data
        logout(request)
        xmpp_backend.remove_user(user.node, user.domain)
        key.delete()
        user.delete()

        return HttpResponseRedirect(reverse('blog:home'))


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


class StopUserSessionView(LoginRequiredMixin, View):
    def delete(self, request, resource):
        user = request.user

        # TODO: improve message
        xmpp_backend.stop_user_session(user.node, user.domain, resource, 'Request via homepage.')
        return HttpResponse('ok')


class DeleteHttpUploadView(LoginRequiredMixin, SingleObjectMixin, View):
    queryset = Upload.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        queryset = queryset.filter(jid=self.request.user.get_username())

        return super(DeleteHttpUploadView, self).get_object(queryset=queryset)

    def delete(self, request, pk):
        self.get_object().delete()
        return HttpResponse('ok')


class ManageGpgView(LoginRequiredMixin, SingleObjectMixin, View):
    queryset = Upload.objects.all()

    def get_object(self, queryset=None):
        queryset = self.request.user.gpg_keys.all()
        return super(ManageGpgView, self).get_object(queryset=queryset)

    def get(self, request, pk):
        key = self.get_object()
        address = request.META['REMOTE_ADDR']
        add_gpg_key_task.delay(user_pk=self.request.user.pk, address=address,
                               fingerprint=key.fingerprint)
        return JsonResponse({
            'status': 'success',
            'message': _('Refreshing GPG key...'),
        })

    def delete(self, request, pk):
        self.get_object().delete()
        return HttpResponse('ok')
