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
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse

from ..utils import canonical_link

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def canonical(name, *args, **kwargs):
    return canonical_link(reverse(name, args=args, kwargs=kwargs))


@register.simple_tag
def canonical_static(path):
    return canonical_link(static(path))
