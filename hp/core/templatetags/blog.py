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
from django.utils.html import format_html

from ..models import BlogPost
from ..models import Page

register = template.Library()


@register.simple_tag
def page(pk, title=None, alt=None, anchor=None):
    page = Page.objects.get(pk=pk)
    title = title or page.title.current
    alt = title or alt
    url = page.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_html('<a href="{}" alt="{}">{}</a>', url, alt, title)


@register.simple_tag
def post(pk, title=None, alt=None, anchor=None):
    post = BlogPost.objects.get(pk=pk)
    title = title or post.title.current
    alt = title or alt
    url = post.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_html('<a href="{}" alt="{}">{}</a>', url, alt, title)
