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

from core.utils import format_link

from ..models import BlogPost
from ..models import Page

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag()
def page_url(pk_or_slug, quiet=True):
    """Returns the URL to the given primary key or slug.

    Parameters
    ----------

    pk_or_slug : int or str
        If an ``int`` is passed, it's assumed to be the primary key of the requested page, otherwise
        it's assumed to be the slug of the page.
    quiet : bool, optional
        Unless ``False``, the function will return an empty string if the page is not found.
        Otherwise, the ``DoesNotExist`` exception is propagated.
    """

    try:
        if isinstance(pk_or_slug, int):
            page = Page.objects.get(pk=pk_or_slug)
        else:
            page = Page.objects.slug(pk_or_slug).get()
    except Page.DoesNotExist:
        if quiet is False:
            raise
        return ''

    return page.get_absolute_url()


@register.simple_tag(takes_context=True)
def page(context, pk, text=None, anchor=None, **attrs):
    """Get a link to a page based on its primary key or slug.

    This template tag allows you to generate a HTML link based on the database primary key or slug
    of a page object. The link (which uses the editable slug) will adapt if the slug is changed. You
    can also pass anchor tag, any keyword arguments will be HTML attributes.

    Example::

        {% page 23 %} -> <a href="/p/slug-of-page-23/">title-of-page-23</a>.
        {% page 23 text="foobar" %} -> <a href="/p/slug-of-page-23/">foobar</a>.
        {% page 23 text="foobar" anchor='foo' class='whatever'%}
           -> <a href="/p/slug-of-page-23/#foo" class="whatever">foobar</a>.

    Parameters
    ----------

    pk : int
        The database primary key of the page to link to. The easiest way to get this is from the
        URL of the admin interface.
    text : str, optional
        The link text to use. If not given, the page title in the current language will be used.
    anchor : str, optional
        Optionally adds an anchor tag to the link.
    **attrs
        Any other keyword arguments will be used as HTML attributes in the link.
    """

    try:
        page = Page.objects.get(pk=pk)
    except Page.DoesNotExist:
        page = Page.objects.filter(slug=pk).first()

        if page is None:
            log.error('%s: Page %s does not exist.', context['request'].path, pk)
            return text or ''

    if text is None and attrs.get('title') is not None:
        log.warn(
            '%s: {%% page %%} tag uses title parameter instead of text - title is now the title attribute!',
            context['request'].path)
        text = attrs['title']
        del attrs['title']

    text = text or page.title.current
    url = page.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_link(url, text, **attrs)


@register.simple_tag(takes_context=True)
def post(context, pk, text=None, anchor=None, **attrs):
    """Get a link to blog post based on its primary key.

    This templatetag works the same as :py:func:`~core.templatetags.blog.page`, except that it
    links to blog posts.
    """
    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        post = BlogPost.objects.filter(slug=pk).first()

        if post is None:
            log.error('%s: BlogPost %s does not exist.', context['request'].path, pk)
            return text or ''

    if text is None and attrs.get('title') is not None:
        log.warn(
            '%s: {%% post %%} tag uses title parameter instead of text - title is now the title attribute!',
            context['request'].path)
        text = attrs['title']
        del attrs['title']

    text = text or post.title.current
    url = post.get_absolute_url()
    if anchor is not None:
        url = '%s#%s' % (url, anchor)

    return format_link(url, text, **attrs)
