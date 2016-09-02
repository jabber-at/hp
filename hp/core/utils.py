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
# If not, see <http://www.gnu.org/licenses

import dns.resolver

from django.conf import settings
from django.core.cache import cache


def check_dnsbl(ip):
    cache_key = 'dnsbl_%s' % ip
    blocks = cache.get(cache_key)

    if blocks is not None:
        return blocks

    blocks = []
    for dnsbl in settings.DNSBL:
        print('checking %s' % dnsbl)
        reason = None
        resolver = dns.resolver.Resolver()
        query = '.'.join(reversed(str(ip).split("."))) + "." + dnsbl

        try:
            answers = resolver.query(query, "A")
        except dns.resolver.NXDOMAIN:  # not blacklisted
            continue

        try:
            reason = resolver.query(query, "TXT")[0]
        except:  # reason is optional
            pass

        blocks.append((answers[0], reason))

    cache.set(cache_key, blocks, 3600)  # cache this for an hour
    return blocks

