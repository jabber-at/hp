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
from django.contrib.auth import logout
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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.views.generic import View
from django.views.generic import DetailView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView
from django.views.generic.edit import FormView
from django.views.generic.edit import UpdateView

from celery import chain
from xmpp_http_upload.models import Upload
from django_xmpp_backends import backend

from core.constants import ACTIVITY_REGISTER
from core.constants import ACTIVITY_RESET_PASSWORD
from core.constants import ACTIVITY_SET_EMAIL
from core.constants import ACTIVITY_SET_PASSWORD
from core.constants import ACTIVITY_FAILED_LOGIN
from core.models import AddressActivity
from core.views import AnonymousRequiredMixin
from core.views import BlacklistMixin
from core.views import DnsBlMixin
from core.views import RateLimitMixin
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
    requires_confirmation = True

    def dispatch(self, request, *args, **kwargs):
        if self.requires_confirmation and not request.user.created_in_backend:
            kwargs = {}
            if isinstance(self, SingleObjectMixin):
                self.object = self.get_object()
                kwargs['object'] = self.object
            context = self.get_context_data(**kwargs)

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


class RegistrationView(BlacklistMixin, DnsBlMixin, RateLimitMixin, AnonymousRequiredMixin,
                       StaticContextMixin, CreateView):
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

            # log user creation, display help message.
            user.log(ugettext_noop('Account created.'), address=address)
            AddressActivity.objects.log(request, ACTIVITY_REGISTER, user=user, note=user.email)

            messages.success(request, _(
                """Successfully created the account %(username)s. A confirmation email was
just sent to the email address you provided (%(email)s). Before you can use
your account, you must click on the confirmation link in that email.""" % {
                    'username': user.username,
                    'email': user.email,
                }))

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, user)

        task = send_confirmation_task.si(
            user_pk=user.pk, purpose=PURPOSE_REGISTER, language=lang, address=address,
            to=user.email, base_url=base_url, hostname=request.site['NAME'])

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

    form_class = ConfirmResetPasswordForm
    queryset = _confirmation_qs.purpose(PURPOSE_REGISTER)
    success_url = reverse_lazy('account:detail')
    template_name = 'account/user_register_confirm.html'

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']
        password = form.cleaned_data['password']

        with transaction.atomic():
            try:
                key = self.queryset.get(key=self.kwargs['key'])
            except Confirmation.DoesNotExist:
                return TemplateResponse(
                    request, 'account/user_register_confirmation_not_found.html', {}, status=404)

            key.user.confirmed = timezone.now()
            key.user.created_in_backend = True
            key.user.save()

            if request.user != key.user:
                logout(request)  # logout any previous user
                key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
                login(request, key.user)

            # Actually create the user on the XMPP server
            backend.create_user(username=key.user.node, domain=key.user.domain, password=password,
                                email=key.user.email)

            key.user.log(ugettext_noop('Email address %(email)s confirmed.'), address,
                         email=key.user.email)
            # TODO: More meaningful help message on a webchat, usable clients, follow updates, ...
            messages.success(request, _(
                "Successfully confirmed your email address. You can now use your account."))

            # Delete the registration key
            key.delete()

        return super(ConfirmRegistrationView, self).form_valid(form)


class LoginView(BlacklistMixin, DnsBlMixin, RateLimitMixin, AnonymousRequiredMixin, FormView):
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


class UserView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:detail'
    requires_confirmation = False


class ResetPasswordView(BlacklistMixin, DnsBlMixin, RateLimitMixin, AnonymousRequiredMixin,
                        FormView):
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


class ConfirmResetPasswordView(FormView):
    form_class = ConfirmResetPasswordForm
    queryset = _confirmation_qs.purpose(PURPOSE_RESET_PASSWORD)
    success_url = reverse_lazy('account:detail')
    template_name = 'account/user_password_reset_confirm.html'

    def form_valid(self, form):
        request = self.request
        address = request.META['REMOTE_ADDR']

        with transaction.atomic():
            key = self.queryset.get(key=self.kwargs['key'])
            backend.set_password(username=key.user.node, domain=key.user.domain,
                                 password=form.cleaned_data['password'])

            key.user.log(ugettext_noop('Set new password.'), address)
            messages.success(request, _('Successfully changed your password.'))

            key.user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(self.request, key.user)
            key.delete()

        return super(ConfirmResetPasswordView, self).form_valid(form)


class NotificationsView(LoginRequiredMixin, AccountPageMixin, UpdateView):

    def get_object(self):
        return self.request.user.notifications

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponse('Ok.')

    usermenu_item = 'account:notifications'
    form_class = NotificationsForm
    template_name = 'account/notifications.html'


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
            'We sent you an email to your new email address %(email)s). Click on the link in it '
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
            # TODO: remove old fallback value
            gpg_keys = key.payload.get('gpg_recv_pub', key.payload.get('gpg_key'))
            if gpg_keys:
                add_gpg_key_task.delay(user_pk=user.pk, address=key.address.address,
                                       language=request.LANGUAGE_CODE, key=gpg_keys)

            user.save()
            key.delete()

            messages.success(request,
                             _('Confirmed email address change to %(email)s.')
                             % {'email': user.email, })
            user.log(ugettext_noop('Confirmed email address change to %(email)s.'),
                     request.META['REMOTE_ADDR'], email=key.to)

            return super(ConfirmSetEmailView, self).get_redirect_url()


class HttpUploadView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    usermenu_item = 'account:xep0363'
    template_name = 'account/xep0363.html'

    def get_context_data(self, **kwargs):
        context = super(HttpUploadView, self).get_context_data(**kwargs)
        context['uploads'] = Upload.objects.filter(jid=context['object'].username)
        return context


class GpgView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
    """Main user settings view (/account)."""

    usermenu_item = 'account:gpg'
    template_name = 'account/user_gpg.html'


class RecentActivityView(LoginRequiredMixin, AccountPageMixin, UserDetailView):
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

    def form_valid(self, form):
        password = form.cleaned_data['password']
        request = self.request
        user = request.user

        if not backend.check_password(user.node, user.domain, password=password):
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
        if not backend.check_password(user.node, user.domain, password=password):
            form.add_error('password', _('The password is incorrect.'))
            return self.form_invalid(form)

        # Verify the confirmation key
        key = get_object_or_404(self.queryset.filter(user=user), key=self.kwargs['key'])

        # Log the user out, delete data
        logout(request)
        backend.remove_user(user.node, user.domain)
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
