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
# <http://www.gnu.org/licenses/.

from datetime import date

from django.conf import settings
from django.core.cache import cache

from .models import MenuItem


def basic(request):
    context = {
        'COPYRIGHT_NOTICE': settings.COPYRIGHT_NOTICE % {
            'brand': request.site['BRAND'],
            'year': date.today().year,
        },
        'os': getattr(request, 'os', 'any'),
        'os_mobile': getattr(request, 'os_mobile', True),
        #'menuitems': MenuItem.objects.all(),
        'site': request.site,
        'default_site': settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST],
        # language switcher
        'other_langs': [(k, v) for k, v in settings.LANGUAGES if k != request.LANGUAGE_CODE],
        'FACEBOOK_PAGE': settings.FACEBOOK_PAGE,
        'TWITTER_HANDLE': settings.TWITTER_HANDLE,
        'DEBUG': settings.DEBUG,
        'WEBCHAT': bool(settings.CONVERSEJS_CONFIG),
        'SIDEBAR_PANELS': settings.SIDEBAR_PANELS,
    }

    # Data that requires database access is cached
    cache_key = 'request_context'
    cached = cache.get(cache_key)
    if cached is None:
        cached = {
            'menuitems': MenuItem.objects.all(),
        }
        for item in cached['menuitems']:
            item.cached_data  # touch cached_data to make sure that all properties serialized

        cache.set(cache_key, cached)
    context.update(cached)

    return context
