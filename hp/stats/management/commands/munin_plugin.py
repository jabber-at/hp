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

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from ...constants import STAT_REGISTER
from ...constants import STAT_REGISTER_CONFIRMED
from ...constants import STAT_RESET_PASSWORD
from ...constants import STAT_RESET_PASSWORD_CONFIRMED
from ...constants import STAT_SET_PASSWORD
from ...constants import STAT_SET_EMAIL
from ...constants import STAT_SET_EMAIL_CONFIRMED
from ...constants import STAT_DELETE_ACCOUNT
from ...constants import STAT_DELETE_ACCOUNT_CONFIRMED
from ...constants import STAT_FAILED_LOGIN
from ...models import Event

User = get_user_model()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--config', action='store_true', default=False)

    def unused_percentage(self, now, days):
        # We get users that registered in the last 14 days (new()) and before the threshold
        qs = User.objects.confirmed().new().filter(confirmed__lt=now - timedelta(days=days))
        total = qs.count()
        if total == 0:
            return 100

        return (qs.unused().count() * 100) / total

    def handle(self, *args, **options):
        if options['config']:
            print('''multigraph homepage
graph_args --base 1000 -l 0
graph_category homepage
graph_scale no
graph_title Account activity
graph_vlabel no/24 hours
graph_info Activity on homepage
register.label Registrations
register_confirmed.label Registrations - confirmed
password_reset.label Password resets
password_reset_confirmed.label Password resets - confirmed
set_password.label Set password
set_email.label New email addresses
set_email_confirmed.label New email addresses - confirmed
delete_account.label Account deletions
delete_account_confirmed.label Account deletions - confirmed
failed_logins.label Failed logins
failed_logins.info Does not include XMPP logins
multigraph homepage_unused_accounts
graph_args --base 1000 -l 0 -u 100
graph_category homepage
graph_scale no
graph_title Unused accounts
graph_vlabel Percent
graph_info Percentage of new/confirmed accounts that were not used in the respective timespan.
one_day.label One day
one_day.info Accounts not used one day after confirmation.
three_days.label Three days
three_days.info Accounts not used three days after confirmation.
seven_days.label Seven days
seven_days.info Accounts not used seven days after confirmation.''')
        else:
            now = timezone.now()

            since = now - timedelta(hours=24)
            qs = Event.objects.filter(stamp__gt=since).values_list('metric').order_by('metric')
            values = dict(qs.annotate(count=Count('metric')))

            print('''multigraph homepage
register.value %(register)s
register_confirmed.value %(register_confirmed)s
password_reset.value %(password_reset)s
password_reset_confirmed.value %(password_reset_confirmed)s
set_password.value %(set_password)s
set_email.value %(set_email)s
set_email_confirmed.value %(set_email_confirmed)s
delete_account.value %(delete_account)s
delete_account_confirmed.value %(delete_account_confirmed)s
failed_logins.value %(failed_logins)s
multigraph homepage_unused_accounts
one_day.value %(unused_one)s
three_days.value %(unused_three)s
seven_days.value %(unused_seven)s''' % {
                'register': values.get(STAT_REGISTER, 0),
                'register_confirmed': values.get(STAT_REGISTER_CONFIRMED, 0),
                'password_reset': values.get(STAT_RESET_PASSWORD, 0),
                'password_reset_confirmed': values.get(STAT_RESET_PASSWORD_CONFIRMED, 0),
                'set_password': values.get(STAT_SET_PASSWORD, 0),
                'set_email': values.get(STAT_SET_EMAIL, 0),
                'set_email_confirmed': values.get(STAT_SET_EMAIL_CONFIRMED, 0),
                'delete_account': values.get(STAT_DELETE_ACCOUNT, 0),
                'delete_account_confirmed': values.get(STAT_DELETE_ACCOUNT_CONFIRMED, 0),
                'failed_logins': values.get(STAT_FAILED_LOGIN, 0),
                'unused_one': self.unused_percentage(now, 1),
                'unused_three': self.unused_percentage(now, 3),
                'unused_seven': self.unused_percentage(now, 7),
            })
