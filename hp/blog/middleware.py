# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

import logging

from django.conf import settings
from django.core.cache import cache

from .models import Page

log = logging.getLogger(__name__)


def blog_middleware(get_response):
    """Add CLIENTS_URL and FAQ_URL to request if CLIENTS_PAGE/FAQ_PAGE settings are defined."""

    def middleware(request):
        if settings.CLIENTS_PAGE is not None or settings.FAQ_PAGE is not None:
            cache_key = 'request_context_blog'
            ctx = cache.get(cache_key)

            if ctx is None:
                ctx = {}
                if settings.CLIENTS_PAGE is not None:
                    try:
                        page = Page.objects.pk_or_slug(settings.CLIENTS_PAGE)
                    except Page.DoesNotExist:
                        log.error('CLIENTS_PAGE "%s" does not exist.', settings.CLIENTS_PAGE)
                    finally:
                        ctx['CLIENTS_URL'] = page.get_absolute_url()

                if settings.FAQ_PAGE is not None:
                    try:
                        page = Page.objects.pk_or_slug(settings.FAQ_PAGE)
                    except Page.DoesNotExist:
                        log.error('FAQ_PAGE "%s" does not exist.', settings.FAQ_PAGE)
                    finally:
                        ctx['FAQ_URL'] = page.get_absolute_url()

                cache.set(cache_key, ctx)
        else:
            ctx = {}

        request.hp_request_context_blog = ctx

        return get_response(request)
    return middleware
