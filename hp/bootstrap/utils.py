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

import re
from collections import OrderedDict


def clean_classes(classes):
    """Clean a string of CSS classes or a list of classes.

    >>> clean_classes(' foo   bar     bla foo   ')
    'foo bar bla'
    """
    if isinstance(classes, str):
        # clean multiple whitespaces and split
        classes = re.sub(' +', ' ', classes).strip().split()

    # OrderedDict.fromkeys removes duplicates
    return ' '.join(list(OrderedDict.fromkeys(classes)))


def clean_class_attrs(attrs):
    """Clean classes so that every class occurs only once and each class is separated by exactly one space.

    The order of returned classes is in order of first appearance.

    >>> attrs = {'class': ' foo  bar   whatever bar '}
    >>> clean_class_attrs(attrs)
    >>> attrs
    {'class': 'foo bar whatever'}
    """
    if not attrs.get('class'):
        return

    attrs['class'] = clean_classes(attrs['class'])
