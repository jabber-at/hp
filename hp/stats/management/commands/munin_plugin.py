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

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from ...models import Event


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--config', action='store_true', default=False)

    def handle(self, *args, **options):
        if options['config']:
            print('''graph_args --base 1000 -l 0
graph_category homepage
graph_scale no
graph_title Homepage activity
graph_vlabel no/24 hours
graph_info Activity on homepage
register.label Registrations
register_confirmed.label Confirmed registrations
password_reset.label Password resets
set_email.label New email addresses
delete_account.label Account deletions''')
        else:
            since = timezone.now() - timedelta(hours=24)
            qs = Event.objects.filter(stamp__gt=since).values_list('metric').order_by('metric')
            for key, value in qs.annotate(count=Count('metric')):
                print('%s.value %s' % (key, value))
