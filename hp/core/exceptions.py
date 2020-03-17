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

from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _


class HomepageException(Exception):
    """Base class for all custom exceptions from this homepage."""
    pass


class HttpResponseException(HomepageException):
    """An exception that should yield in a custom HTTP response.

    This is similar to :py:exception:`django:django.http.response.Http404`. Raise a subclass of
    this exception to generate a custom error response.
    """

    context = None
    content_type = None
    status = None
    template = 'error.html'
    title = None

    def __init__(self, *args, template=None, context=None, status=None, **kwargs):
        # Only set self-values if actual values are passed, this way the class values of
        # subclasses remain the default
        if template is not None:
            self.template = template
        if context is None:
            self.context = {}
        else:
            self.context = context
        if status is not None:
            self.status = status

        super(HttpResponseException, self).__init__(*args, **kwargs)

        if self.template is None:
            raise ValueError(
                "Exception does not define template and constructor didn't receive any.")

    def get_response(self, request, default_context=None):
        if default_context is None:
            default_context = {}
        default_context.update(self.context)
        default_context['exception'] = self

        return TemplateResponse(
            request, template=self.template, context=default_context,
            content_type=self.content_type, status=self.status)

    def get_title(self):
        if self.title:
            return self.title
        return self.__class__.__name__


class TemporaryError(HttpResponseException):
    status = 503
    title = _('Temporary error')
