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
# If not, see <http://www.gnu.org/licenses/.

from django.conf import settings

from .models import MenuItem


def basic(request):
    context = {
        'menuitems': MenuItem.objects.all(),
        'site': request.site,
        'default_site': settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST],
        # language switcher
        'other_langs': [(k, v) for k, v in settings.LANGUAGES if k != request.LANGUAGE_CODE],
        'FACEBOOK_PAGE': settings.FACEBOOK_PAGE,
        'FACEBOOK_PAGE_ID': settings.FACEBOOK_PAGE_ID,
        'TWITTER_HANDLE': settings.TWITTER_HANDLE,
    }
    return context
