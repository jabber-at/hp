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
# You should have received a copy of the GNU General Public License along with this project. If
# not, see <http://www.gnu.org/licenses/>.

import logging

from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from ..utils import format_timedelta as _format_timedelta

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def path(urlname, text='', alt=None, anchor=None, **kwargs):
    if not text:
        log.warn('No text received path %s', urlname)
        text = urlname

    try:
        path = reverse(urlname, kwargs=kwargs)
        if anchor is not None:
            path = '%s#%s' % (path, anchor)

        alt = alt or text

        return format_html('<a href="{}" alt="{}">{}</a>', path, alt, text)
    except Exception as e:
        log.exception(e)
        return ''


@register.filter
def format_timedelta(delta):
    """Passes the delta to :py:func:`core.utils.format_timedelta`."""

    return _format_timedelta(delta)
