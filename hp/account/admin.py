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

from xmpp_backends.base import UserNotFound
from xmpp_backends.django import xmpp_backend

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_object_actions import DjangoObjectActions

from .constants import PURPOSE_REGISTER
from .forms import AdminUserForm
from .models import Confirmation
from .models import GpgKey
from .models import User
from .models import UserLogEntry
from .tasks import resend_confirmations
from .tasks import send_confirmation_task

log = logging.getLogger(__name__)


class ConfirmedFilter(admin.SimpleListFilter):
    title = _('confirmed email')
    parameter_name = 'confirmed'

    def lookups(self, request, model_admin):
        return (
            ('0', 'No'),
            ('1', 'Yes'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(confirmed__isnull=True)
        elif self.value() == '1':
            return queryset.filter(confirmed__isnull=False)
        return queryset


class CreatedInBackendFilter(admin.SimpleListFilter):
    title = _('created in backend')
    parameter_name = 'in_backend'

    def lookups(self, request, model_admin):
        return (
            ('0', 'No'),
            ('1', 'Yes'),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(created_in_backend=False)
        elif self.value() == '1':
            return queryset.filter(created_in_backend=True)
        return queryset


@admin.register(User)
class UserAdmin(DjangoObjectActions, BaseUserAdmin):
    actions = ['send_registration', 'block_users', ]
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email'),
        }),
    )
    change_actions = ['block_user', ]
    fieldsets = (
        (None, {
            'fields': ('username', 'email', ('registered', 'confirmed', 'last_activity', ),
                       'registration_method', 'blocked', 'default_language', ),
        }),
    )
    form = AdminUserForm
    list_display = ('username', 'email', 'registered', 'confirmed', 'last_activity', )
    list_filter = (ConfirmedFilter, CreatedInBackendFilter, 'is_superuser', )
    ordering = ('-registered', )
    readonly_fields = ['username', 'registered', 'blocked', ]
    search_fields = ['username', 'email', ]

    def send_registration(self, request, queryset):
        base_url = '%s://%s' % (request.scheme, request.get_host())

        for user in queryset.filter(created_in_backend=False):
            # Try to get any existing confirmation and resend it if it exists
            conf = user.confirmations.filter(purpose=PURPOSE_REGISTER).first()
            if conf is not None:
                resend_confirmations.delay(conf.pk)

            # No confirmation key exists (anymore), so we create a new one from existing data
            else:
                send_confirmation_task.delay(
                    user_pk=user.pk, purpose=PURPOSE_REGISTER, language='en', to=user.email,
                    base_url=base_url, hostname=user.domain)
    send_registration.short_description = _('Send new registration confirmations')

    def block_user(self, request, obj):
        obj.blocked = True
        obj.save()
        try:
            xmpp_backend.block_user(obj.node, obj.domain)
        except UserNotFound:
            pass
    block_user.label = _('Block')
    block_user.short_description = _('Block this user')

    def block_users(self, request, queryset):
        queryset.update(blocked=True)
        for user in queryset:
            try:
                xmpp_backend.block_user(user.node, user.domain)
            except UserNotFound:
                continue
    block_users.short_description = _('Block selected users')


@admin.register(UserLogEntry)
class UserLogEntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'address', 'created')
    search_fields = ('message', 'address', 'user__username', 'user__email', )
    ordering = ('-created', )


@admin.register(GpgKey)
class GpgKeyAdmin(admin.ModelAdmin):
    actions = ['refresh']
    list_display = ('user', 'fingerprint', 'expires', 'valid', 'usable')
    list_select_related = ('user', )
    list_filter = ('revoked', )
    ordering = ('-created', )
    search_fields = ('fingerprint', 'user__username', 'user__email', )

    def valid(self, obj):
        return not obj.revoked  # just the inverse, more intuitive
    valid.boolean = True

    def usable(self, obj):
        now = timezone.now()
        if obj.expires:
            return obj.expires > now and not obj.revoked
        else:
            return not obj.revoked
    usable.boolean = True

    def refresh(self, request, queryset):
        for obj in queryset:
            try:
                obj.refresh()
            except Exception as e:
                log.exception(e)
                messages.error(request, _('Error importing %(fingerprint)s: %(error)s') % {
                    'fingerprint': obj.fingerprint,
                    'error': e,
                })
    refresh.short_description = _('Refresh keys from keyserver')


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    actions = ['resend']
    list_display = ('key', 'user', 'address', 'purpose', 'to', 'expires', )
    list_filter = ('purpose', )
    list_select_related = ('user', 'address', )
    search_fields = ('key', 'to', 'user__username', 'user__email', )

    def resend(self, request, queryset):
        resend_confirmations.delay(*queryset.values_list('pk', flat=True))
    resend.short_description = _('Resend confirmations')


admin.site.unregister(Group)
