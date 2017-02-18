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

import tempfile

import requests
from celery import shared_task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.core import files

from .models import Image

log = get_task_logger(__name__)


@shared_task
def download_xmpp_net_badges():
    for host in settings.XMPP_HOSTS:
        filename = 'badge_%s.svg' % host.replace('.', '_')
        try:
            image = Image.objects.get(name=filename)
        except Image.DoesNotExist:
            image = Image(name=filename)

        response = requests.get('https://xmpp.net/badge.php', params={'domain': host}, stream=True)
        if response.status_code != requests.codes.ok:
            log.error('Could not download badge for %s.', host)
            continue

        with tempfile.NamedTemporaryFile() as stream:
            for block in response.iter_content(1024 * 8):
                if not block:
                    break
                stream.write(block)

            image.image.save(filename, files.File(stream))
