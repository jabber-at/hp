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

import logging

from django.core.urlresolvers import reverse

from .models import MenuItem
from .models import BlogPost
from .models import Page

log = logging.getLogger(__name__)


"""
These two objects act as proxy to get permalinks in TinyMCE.

What we'd actually want is html using Djangos ``url`` template tag::

    <a href="{% url "core:page" slug="features" %}">...</a>

You can't set this in TinyMCE because spaces are escaped (to "%20") so that doesn't work.

The best solution would be to add a custom TinyMCE editor button adding links like this.
But django-tinymce uses version 3.x, 4.x is underway and changes everything, so
no work on that now.

The ugly solution are the below proxy models in the context: ``__getitem__`` makes this
act like a dictionary, so you can do::

    >>> p = Pages()
    >>> p[1]
    "p/foobar/"

... assuming that the page with the id 1 has the slug "foobar". In a template
(and Pages and BlogPosts are interpreted as templates), you would do::

    {{url.1}}

The result is without a leading slash, because TinyMCE appends the current path if there is no
leasing slash. So to get a currect link, with TinyMCE, add this to the "Target" field when adding
a link::

    /{{url.1}}

"""
class Pages(object):
    def __getitem__(self, name):
        try:
            p = Page.objects.get(pk=name)
        except Page.DoesNotExist:
            log.error('Error getting page with pk %s.', name)
            return ''
        return reverse('core:page', kwargs={'slug': p.slug.current})[1:]


class Posts(object):
    def __getitem__(self, name):
        try:
            p = BlogPost.objects.get(pk=name)
        except BlogPost.DoesNotExist:
            log.error('Error getting page with pk %s.', name)
            return ''
        return reverse('core:page', kwargs={'slug': p.slug.current})[1:]


def basic(request):
    context = {
        'menuitems': MenuItem.objects.all(),
        'site': request.site,
        'pages': Pages(),
        'posts': Posts(),
    }
    return context
