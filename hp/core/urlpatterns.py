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

from django.conf import settings
from django.urls import RegexURLPattern
from django.urls import RegexURLResolver
from django.urls import Resolver404
from django.utils import translation


class LocaleRegexURLResolver(RegexURLResolver):
    """URLResolver that tries all languages for URL resolving.

    First tries to resolve the URL in the currently used language, then tries all other languages.
    An attribute is attached to the function to let the TranslatedUrlConfigMiddleware know if the
    match was in a translated language, so it can redirect to the proper URL.
    """

    def resolve(self, path):
        try:
            match = super(LocaleRegexURLResolver, self).resolve(path)
            # NOTE 1: Do not set translated_match on the match itself, because the match is copied
            #         by Djangos root URL resolver and any unknown properties are not copied.
            # NOTE 2: We set this to False because matches are cached by Django, so a match would
            #         be marked as translated as soon as it was visited once with an alternate
            #         language.
            match.func.translated_match = False
            return match
        except Resolver404 as e:
            other_langs = [k for k, v in settings.LANGUAGES if k != translation.get_language()]

            for code in other_langs:
                with translation.override(code):
                    try:
                        match = super(LocaleRegexURLResolver, self).resolve(path)
                        match.func.translated_match = True
                        return match
                    except Resolver404:
                        continue
            raise e


def i18n_url(regex, view, kwargs=None, name=None, prefix=''):
    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        urlconf_module, app_name, namespace = view
        return LocaleRegexURLResolver(regex, urlconf_module, kwargs, app_name=app_name,
                                      namespace=namespace)
    else:
        return RegexURLPattern(regex, view, kwargs, name)
