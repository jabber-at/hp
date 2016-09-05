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

import os
import dns.resolver

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ungettext
from django.utils.translation import ugettext as _


def format_timedelta(delta):
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _seconds = divmod(rem, 60)

    # Get translated strings for days/hours/minutes
    if days:
        days = ungettext('one day', '%(count)d days', days) % {'count': days}
    if hours:
        hours = ungettext('one hour', '%(count)d hours', hours) % {'count': hours}
    if minutes:  # just minutes
        minutes = ungettext('one minute', '%(count)d minutes', minutes) % {'count': minutes}

    # Assemble a string based on what we have
    if days and hours and minutes:
        return _('%(days)s, %(hours)s and %(minutes)s') % {
            'days': days, 'hours': hours, 'minutes': minutes, }
    elif days and hours:
        return _('%(days)s and %(hours)s') % {'days': days, 'hours': hours, }
    elif days and minutes:
        return _('%(days)s and %(minutes)s') % {'days': days, 'minutes': minutes, }
    elif days:
        return days
    elif hours and minutes:
        return _('%(hours)s and %(minutes)s') % {'hours': hours, 'minutes': minutes, }
    elif hours:
        return hours
    elif minutes:
        return minutes
    else:
        return _('Now')


def load_private_key(domain):
    fp = settings.XMPP_HOSTS[domain].get('GPG_FINGERPRINT')
    if fp:
        path = os.path.join(settings.GPG_KEYDIR, '%s.key' % fp)
        with open(path, 'rb') as stream:
            return fp, stream.read()
    return None, None


def load_contact_keys(domain):
    keys = {}
    fingerprints = settings.XMPP_HOSTS[domain].get('CONTACT_GPG_FINGERPRINTS', [])

    for fp in fingerprints:
        path = os.path.join(settings.GPG_KEYDIR, '%s.pub' % fp)
        with open(path, 'rb') as stream:
            keys[fp] = stream.read()

    return keys

def check_dnsbl(ip):
    """Check the given IP for DNSBL listings.

    This method caches results for an hour to improve speed.
    """

    cache_key = 'dnsbl_%s' % ip
    blocks = cache.get(cache_key)

    if blocks is not None:
        return blocks

    blocks = []
    for dnsbl in settings.DNSBL:
        reason = None
        resolver = dns.resolver.Resolver()
        query = '.'.join(reversed(str(ip).split("."))) + "." + dnsbl

        try:
            resolver.query(query, "A")
        except dns.resolver.NXDOMAIN:  # not blacklisted
            continue

        try:
            reason = resolver.query(query, "TXT")[0].to_text()
        except:  # reason is optional
            pass

        blocks.append((dnsbl, reason))

    cache.set(cache_key, blocks, 3600)  # cache this for an hour
    return blocks

