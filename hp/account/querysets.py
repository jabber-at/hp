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
from django.db import models
from django.utils import timezone


class UserQuerySet(models.QuerySet):
    def has_email(self):
        """Users that have an email address."""
        return self.exclude(email='')

    def confirmed(self):
        """Users that have a confirmed email address."""
        return self.exclude(email='').exclude(confirmed__isnull=True)

    def count_confirmations(self):
        return self.annotate(count_confirmations=models.Count('confirmations', distinct=True))

    def has_no_confirmations(self):
        return self.filter(confirmations__isnull=True).distinct()

    def has_confirmations(self):
        return self.filter(confirmations__isnull=False).distinct()

    def blocked(self):
        return self.filter(blocked=True)

    def not_blocked(self):
        return self.filter(blocked=False)

    def host(self, hostname):
        return self.filter(username__endswith='@%s' % hostname)

    def not_expiring(self, now=None):
        """Filter users with a recent activity."""

        if settings.ACCOUNT_EXPIRES_DAYS is None:
            return self
        if now is None:
            now = timezone.now()

        return self.filter(last_activity__gt=now - settings.ACCOUNT_EXPIRES_NOTIFICATION_DAYS)

    def expiring(self, now=None):
        """Match users currently scheduled for automatic account removal.

        This matches users with a ``last_activity`` on or before the current date minus the delta
        defined by settings.ACCOUNT_EXPIRES_NOTIFICATION_DAYS. If settings.ACCOUNT_EXPIRES_DAYS is
        ``None``, this function always returns an empty queryset.
        """
        if settings.ACCOUNT_EXPIRES_DAYS is None:
            return self.none()

        if now is None:
            now = timezone.now()

        return self.filter(last_activity__lte=now - settings.ACCOUNT_EXPIRES_NOTIFICATION_DAYS)


class GpgKeyQuerySet(models.QuerySet):
    def valid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__gte=now)

    def invalid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__lt=now)


class ConfirmationQuerySet(models.QuerySet):
    def purpose(self, purpose):
        return self.filter(purpose=purpose)

    def valid(self, now=None):
        if now is None:
            now = timezone.now()
        return self.filter(expires__gte=now)

    def expired(self, now=None):
        if now is None:
            now = timezone.now()

        return self.filter(expires__lt=now)


class UserLogEntryQuerySet(models.QuerySet):
    def expired(self, now=None, delta=None):
        if now is None:
            now = timezone.now()
        if delta is None:
            delta = settings.USER_LOGENTRY_EXPIRES

        return self.filter(created__lt=now - delta)
