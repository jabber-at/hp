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

from django import template
from django.core.urlresolvers import reverse
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def render(context, variable):
    variable = '{%% load blog render %%}%s' % variable
    t = template.Template(variable)
    return t.render(context)


@register.simple_tag
def path(urlname, text, alt=None, anchor=None, **kwargs):
    path = reverse(urlname, kwargs=kwargs)
    if anchor is not None:
        path = '%s#%s' % (path, anchor)

    alt = alt or text

    return format_html('<a href="{}" alt="{}">{}</a>', path, alt, text)
