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
def icon(icon, style='fas', tag='span', css_classes='', **attrs):
    """A simple reusable icon with fontawesome.

    >>> icon('trash')
    '<span class="fas fa-trash"></span>'
    >>> icon('font-awesome', style='fab')
    '<span class="fab fa-font-awesome"></span>'
    >>> icon('fas', 'font-awesome', tag='i')
    '<i class="fas fa-font-awesome"></i>'
    >>> icon('fas', 'font-awesome', tag='i', id='some-id')
    '<i class="fas fa-font-awesome" id="some-id"></i>'

    Parameters
    ----------

    icon : str
        The icon to display.
    style : str, optional
        The style to use for the icon. The default is ``"fas"``.
    tag : str, optional
        The HTML tag used for the icon, the default is ``"span"``.
    css_classes : str, optional
        Any additional CSS classes to add.
    **attrs
        Any additional HTML attributes of the icon.
    """

    attrs['class'] = '%s fa-%s' % (style, icon) + css_classes
    return format_html('<{}{}></{}>', tag, flatatt(attrs), tag)


@register.simple_tag
def icon_add(css_classes='', **attrs):
    return icon('plus', **attrs)


@register.simple_tag
def icon_reload(css_classes='', **attrs):
    return icon('sync', **attrs)


@register.simple_tag
def icon_delete(css_classes='', **attrs):
    return icon('trash', **attrs)


@register.simple_tag
def icon_unfolded(css_classes='', **attrs):
    css_classes += ' unfolded'
    return icon('angle-down', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_folded(css_classes='', **attrs):
    css_classes += ' folded'
    return icon('angle-right', css_classes=css_classes, **attrs)
