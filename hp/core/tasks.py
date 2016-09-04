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

from celery import shared_task

from django.utils import timezone

from .models import Address
from .models import AddressActivity
from .models import CachedMessage

from xmpp_http_upload.models import Upload


@shared_task
def cleanup():
    """Remove various accumulating data from the core app."""

    expired = timezone.now() - timedelta(days=31)
    AddressActivity.objects.filter(timestamp__lt=expired).delete()
    Address.objects.count_activities().filter(activities=0).delete()
    CachedMessage.objects.filter(created__lt=expired).delete()

    # Cleanup XEP-0363 uploads
    Upload.objects.cleanup()
