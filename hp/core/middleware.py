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
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http.request import split_domain_port
from django.http.request import validate_host
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from xmpp_backends.base import BackendError

from .exceptions import HttpResponseException
from .models import CachedMessage

log = logging.getLogger(__name__)


class SiteMiddleware(object):
    def process_request(self, request):
        host = request._get_raw_host()
        domain, port = split_domain_port(host)

        for name, config in settings.XMPP_HOSTS.items():
            if validate_host(domain, config['ALLOWED_HOSTS']):
                request.site = config
                return

        request.site = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]


class TranslatedUrlConfigMiddleware(object):
    """Middleware to handle translated paths."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        if getattr(match.func, 'translated_match', False):
            url_name = match.url_name  # "name" parameter in the URL config
            if match.namespace:
                url_name = '%s:%s' % (match.namespace, url_name)

            return HttpResponseRedirect(reverse(url_name))


class CeleryMessageMiddleware(object):
    def process_request(self, request):
        if request.user.is_anonymous():
            return

        with transaction.atomic():
            stored_msgs = CachedMessage.objects.filter(user=request.user)
            if stored_msgs:
                for msg in stored_msgs:
                    messages.add_message(request, msg.level, _(msg.message) % msg.payload)

                stored_msgs.delete()


class HttpResponseExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, HttpResponseException):
            log.exception(exception)
            return exception.get_response(request)
        if isinstance(exception, BackendError):
            log.exception(exception)
            return TemplateResponse(
                request, template='core/errors/xmpp_backend.html', status=503)
