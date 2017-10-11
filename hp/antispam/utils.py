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
# You should have received a copy of the GNU General Public License along with this project.
# If not, see <http://www.gnu.org/licenses/>.

GMAIL_DOMAINS = set(['google.com', 'googlemail.com', 'gmail.com'])


def normalize_email(value):
    local, domain = value.strip().lower().rsplit('@', 1)
    local = local.split('+', 1)[0]

    if domain in GMAIL_DOMAINS:
        # gmail domains support dot-aliasing: foobar@gmail.com is the same as f.o.o.b.a.r@gmail.com.
        local = local.replace('.', '')

    return '%s@%s' % (local, domain)
