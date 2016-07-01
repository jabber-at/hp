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
from django.core.urlresolvers import Resolver404
from django.core.urlresolvers import Http404
from django.core.urlresolvers import resolve
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import translation


class SiteMiddleware(object):
    def process_request(self, request):
        host = request.META.get('HTTP_HOST', request.META.get('SERVER_NAME'))
        config = getattr(settings, 'XMPP_HOSTS_MAPPING', {}).get(host)
        if config is None:
            config = settings.DEFAULT_XMPP_HOST

        request.site = settings.XMPP_HOSTS[config]
        request.site['DOMAIN'] = config
        request.site.setdefault('BRAND', getattr(settings, 'BRAND', config))


class TranslatedUrlConfigMiddleware(object):
    """Middleware to handle translated paths.

    Some URL paths are translated (e.g. /contact/ and /kontakt/). Paths only work for the currently
    active language, so /kontakt/ raises Http404 if the user uses English, and /contact/ if the
    user uses German.

    This Middleware catches Http404 exceptions and tries to resolve the current path in all other
    configured languages. If a match is found, we use its URL name to resolve the path in the
    current language and redirect to it.

    This middleware only handles translation strings in URL configs (= urls.py files in apps). It
    does not handle e.g. slugs for blog-posts or pages, these are handled by the view itself (see
    :py:class:`~core.views.TranslateSlugViewMixin`).

    .. TODO:: This does not yet handle querystrings
    """

    def process_exception(self, request, exception):
        if not isinstance(exception, Http404):
            return

        # get a list of all languages except the currently active one
        other_langs = [k for k, v in settings.LANGUAGES if k != request.LANGUAGE_CODE]

        match = None
        for code in other_langs:
            with translation.override(code):
                try:
                    match = resolve(request.path)
                    break
                except Resolver404:
                    continue

        if match is not None:
            url_name = match.url_name  # "name" parameter in the URL config
            if match.namespace:
                urlname = '%s:%s' % (match.namespace, url_name)

            return HttpResponseRedirect(reverse(urlname))
