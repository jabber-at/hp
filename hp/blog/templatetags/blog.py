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
from django.utils.html import format_html

from ..models import BlogPost
from ..models import Page

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag(takes_context=True)
def page(context, pk, title=None, anchor=None):
    """Get a link to a page based on its primary key.

    This template tag allows you to generate a HTML link based on the database primary key of a
    page object. The link (which uses the editable slug) will adapt if the slug is changed.

    Example::

        {% page 23 %} -> <a href="/p/slug-of-page-23/">title-of-page-23</a>.
        {% page 23 title="foobar" %} -> <a href="/p/slug-of-page-23/">foobar</a>.

    Parameters
    ----------

    pk : int
        The database primary key of the page to link to. The easiest way to get this is from the
        URL of the admin interface.
    title : str, optional
        The link to use. If not given, the page title in the current language will be used.
    anchor : str, optional
        Optionally adds an anchor tag to the link.
    """

    try:
        page = Page.objects.get(pk=pk)
    except Page.DoesNotExist:
        log.error('%s: Page %s does not exist.', context['request'].path, pk)
        return title or ''

    title = title or page.title.current
    url = page.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_html('<a href="{}">{}</a>', url, title)


@register.simple_tag(takes_context=True)
def post(context, pk, title=None, anchor=None):
    """Get a link to blog post based on its primary key.

    This templatetag works the same as :py:func:`~core.templatetags.blog.page`, except that it
    links to blog posts.
    """
    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        log.error('%s: BlogPost %s does not exist.', context['request'].path, pk)
        return title or ''

    title = title or post.title.current
    url = post.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_html('<a href="{}">{}</a>', url, title)
