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

import logging
import os
import re
import textwrap

from urllib.parse import urljoin

import dns.resolver
import html5lib

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ungettext
from django.utils.translation import ugettext as _
from django.utils.text import normalize_newlines

from .exceptions import TemporaryError

log = logging.getLogger(__name__)


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


def load_private_key(hostname):
    fp = settings.XMPP_HOSTS[hostname].get('GPG_FINGERPRINT')
    if fp:
        path = os.path.join(settings.GPG_KEYDIR, '%s.key' % fp)
        with open(path, 'rb') as stream:
            key = stream.read()

        path = os.path.join(settings.GPG_KEYDIR, '%s.pub' % fp)
        with open(path, 'rb') as stream:
            pub = stream.read()
        return fp, key, pub
    return None, None, None


def load_contact_keys(hostname):
    keys = {}
    fingerprints = settings.XMPP_HOSTS[hostname].get('CONTACT_GPG_FINGERPRINTS', [])

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
        except (dns.resolver.NoNameservers, dns.exception.Timeout):
            # Nameservers are unreachable
            raise TemporaryError(
                _("Could not check DNS-based blocklists. Please try again later."))
        except dns.resolver.NXDOMAIN:  # not blacklisted
            continue

        try:
            reason = resolver.query(query, "TXT")[0].to_text()
        except:  # reason is optional
            pass

        blocks.append((dnsbl, reason))

    cache.set(cache_key, blocks, 3600)  # cache this for an hour
    return blocks


def canonical_link(path):
    """Get the canonical link of a relative URL path.

    Uses the ``CANONICAL_BASE_URL`` setting in the default ``XMPP_HOST`` as base URL.

    Example::

        >>> canonical_link('/foo/bar')
        'https://example.com/foo/bar'
    """
    base_url = settings.XMPP_HOSTS[settings.DEFAULT_XMPP_HOST]['CANONICAL_BASE_URL']
    return urljoin(base_url, path)


def absolutify_html(html, base_url):
    """Make relative links in the given html absolute.

    This code is copied from `here <http://garethrees.org/2009/10/09/feed/>`_.

    Examle::

        >>> absolutify_html('<a href="/foobar">test</a>', 'https://example.com')
        '<a href="https://example.com/foobar">test</a>
    """

    attributes = [
        ('a', 'href'),
        ('img', 'src'),
        ('link', 'href'),
        ('script', 'src')
    ]

    # Parse SRC as HTML.
    tree_builder = html5lib.treebuilders.getTreeBuilder('dom')
    parser = html5lib.html5parser.HTMLParser(tree=tree_builder)
    dom = parser.parse(html)

    # Change all relative URLs to absolute URLs by resolving them relative to
    # BASE_URL. Note that we need to do this even for URLs that consist only of
    # a fragment identifier, because Google Reader changes href=#foo to
    # href=http://site/#foo
    for tag, attr in attributes:
        for e in dom.getElementsByTagName(tag):
            u = e.getAttribute(attr)
            if u:
                e.setAttribute(attr, urljoin(base_url, u))

    # Return the HTML5 serialization of the <BODY> of the result (we don't want
    # the <HEAD>: this breaks feed readers).
    body = dom.getElementsByTagName('body')[0]
    tree_walker = html5lib.treewalkers.getTreeWalker('dom')
    html_serializer = html5lib.serializer.htmlserializer.HTMLSerializer()
    return ''.join(html_serializer.serialize(tree_walker(body)))


def mailformat(text, width=78):
    text = normalize_newlines(text.strip())
    text = re.sub('\n\n+', '\n\n', text)

    ps = []
    for p in text.split('\n\n'):
        ps.append(textwrap.fill(p, width=width))
        ps.append('')

    return '\n'.join(ps).strip()
