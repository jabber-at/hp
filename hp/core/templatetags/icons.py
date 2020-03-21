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

#from django.utils.translation import gettext as _

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def icon(icon, style='fas', tag='span', css_classes='', **attrs):
    """A simple reusable icon with fontawesome.

    >>> icon('trash')
    '<span class="fas fa-trash"></span>'
    >>> icon('font-awesome', style='fab')
    '<span class="fab fa-font-awesome"></span>'
    >>> icon('font-awesome', style='fab', tag='i')
    '<i class="fab fa-font-awesome"></i>'
    >>> icon('font-awesome', style='fab', tag='i', id='some-id')
    '<i class="fab fa-font-awesome" id="some-id"></i>'

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
def icon_success(text_class='success', css_classes='', **kwargs):
    css_classes += ' text-%s icon-success' % text_class
    return icon('check', css_classes=css_classes, **kwargs)


@register.simple_tag
def icon_error(text_class='danger', css_classes='', **kwargs):
    css_classes += ' text-%s icon-error' % text_class
    return icon('times', css_classes=css_classes, **kwargs)


@register.simple_tag
def icon_question(text_class='muted', css_classes='', **kwargs):
    css_classes += ' text-%s icon-question' % text_class
    return icon('question', css_classes=css_classes, **kwargs)


@register.simple_tag
def icon_add(css_classes='', **attrs):
    return icon('plus', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_reload(css_classes='', **attrs):
    return icon('sync', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_delete(css_classes='', **attrs):
    return icon('trash', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_unfolded(css_classes='', **attrs):
    css_classes += ' icon-unfolded'
    return icon('angle-down', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_folded(css_classes='', **attrs):
    css_classes += ' icon-folded'
    return icon('angle-right', css_classes=css_classes, **attrs)


@register.simple_tag
def icon_warning(css_classes='', **attrs):
    css_classes += ' icon-warning'
    return icon('exclamation', css_classes=css_classes, **attrs)


@register.simple_tag(takes_context=True)
def button_reload(context, *, action, url, title, css_classes='', hidden=True, **attrs):
    css_classes += ' hover-success icon-button'
    attrs.setdefault('data-action', action)
    attrs['title'] = title
    attrs['data-url'] = url

    if hidden is True:
        attrs['aria-hidden'] = 'true'

    text = format_html('<span class="sr-only">{}</span>', title)
    return text + icon_reload(css_classes=css_classes, **attrs)


@register.simple_tag(takes_context=True)
def button_delete(context, *, action, url, title, css_classes='', hidden=True, **attrs):
    css_classes += ' hover-danger icon-button'
    attrs.setdefault('data-action', action)
    attrs.setdefault('data-type', 'DELETE')
    attrs['title'] = title
    attrs['data-url'] = url

    if hidden is True:
        attrs['aria-hidden'] = 'true'

    text = format_html('<span class="sr-only">{}</span>', title)
    return text + icon_delete(css_classes=css_classes, **attrs)
