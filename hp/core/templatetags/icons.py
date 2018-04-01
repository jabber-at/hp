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

import logging

from django import template
from django.forms.utils import flatatt
#from django.urls import reverse
#from django.utils.html import mark_safe
from django.utils.html import format_html

#from django.utils.translation import ugettext as _

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def icon(style, icon, tag='span', **attrs):
    """A simple reusable icon with fontawesome.

    >>> icon('fas', 'font-awesome')
    '<span class="fas fa-font-awesome"></span>'
    >>> icon('fas', 'font-awesome', tag='i')
    '<i class="fas fa-font-awesome"></i>'
    >>> icon('fas', 'font-awesome', tag='i', id='some-id')
    '<i class="fas fa-font-awesome" id="some-id"></i>'
    """

    css_classes = '%s fa-%s' % (style, icon)

    if attrs.get('class'):
        attrs['class'] = css_classes + attrs['class']
    else:
        attrs['class'] = css_classes

    return format_html('<{}{}></{}>', tag, flatatt(attrs), tag)
