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
from django.utils.translation import ugettext as _

from ..forms import SelectOSForm
from ..utils import format_link
from ..utils import format_timedelta as _format_timedelta
from ..utils import mailformat

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def path(urlname, text='', title=None, anchor=None, **kwargs):
    """Return a HTML link to the given urlname.

    The difference to this tag and Django's builtin ``{% url %}`` template tag is that this tag
    returns a complete HTML link. The primary use is to use dynamic links to paths in rendered blog
    posts or pages.

    Parameters
    ----------

    urlname : str
        The URL name to resolve and link to. URL names are configured in an apps ``url.py``,
        examples are ``"account:register"`` or ``"feed:rss2"``.
    text : str
        The link text. If omitted, a warning is logged and the ``urlname`` will be used instead.
    title : str, optional
        A link title attribute.

        .. seealso:: https://www.w3.org/TR/html401/struct/links.html#h-12.1.4

    anchor : str, optional
        Any HTML anchor to be added to the resolved URL.
    **kwargs
        Any keyword arguments will be passed as kwargs to the URL resolver.

    """
    if not text:
        log.warn('No text received path %s', urlname)
        text = urlname

    try:
        path = reverse(urlname, kwargs=kwargs)
        if anchor is not None:
            path = '%s#%s' % (path, anchor)

        return format_link(path, text, title=title)
    except Exception as e:
        log.exception(e)
        return ''


@register.filter
def format_timedelta(delta):
    """Passes the delta to :py:func:`core.utils.format_timedelta`."""

    return _format_timedelta(delta)


@register.filter
def format_filesize(size):
    """Format a filesize according to the current translation.

    A few example, given the template::

        {% format_filesize 200 %}
        {% format_filesize 3000 %}
        {% format_filesize 30000000 %}

    You will get::

        200 bytes
        2.93 kilobyte
        28.61 megabyte

    """
    if size < 2000:
        return _('%s bytes') % size
    elif size < 1024 * 900:  # starting at ~900 KB, we display in MB
        return _('%.2f kilobyte') % (size / 1024)
    else:
        return _('%.2f megabyte') % (size / 1024 / 1024)


@register.simple_tag(takes_context=True)
def os_selector(context):
    """Display a selector for OS-specific content."""
    form = SelectOSForm()
    return format_html('<form class="form-horizontal">{}</form>', form['os'].formgroup())


@register.tag('mailformat')
def do_mailformat(parser, token):
    """Tag to format the enclosed text as a plain-text email."""

    nodelist = parser.parse(('endmailformat',))
    parser.delete_first_token()
    return UpperNode(nodelist)


class UpperNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        return mailformat(self.nodelist.render(context))
