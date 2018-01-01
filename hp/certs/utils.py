# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

from cryptography import x509
from cryptography.x509.oid import NameOID

SAN_NAME_MAPPINGS = {
    x509.DNSName: 'DNS',
    x509.RFC822Name: 'email',
    x509.DirectoryName: 'dirname',
    x509.UniformResourceIdentifier: 'URI',
    x509.IPAddress: 'IP',
    x509.RegisteredID: 'RID',
    x509.OtherName: 'otherName',
}

#: Map OID objects to IDs used in subject strings
OID_NAME_MAPPINGS = {
    NameOID.COUNTRY_NAME: 'C',
    NameOID.STATE_OR_PROVINCE_NAME: 'ST',
    NameOID.LOCALITY_NAME: 'L',
    NameOID.ORGANIZATION_NAME: 'O',
    NameOID.ORGANIZATIONAL_UNIT_NAME: 'OU',
    NameOID.COMMON_NAME: 'CN',
    NameOID.EMAIL_ADDRESS: 'emailAddress',
}


def format_name(subject):
    """Convert a subject into the canonical form for distinguished names.

    This function does not take care of sorting the subject in any meaningful order.

    Examples::

        >>> format_name([('CN', 'example.com'), ])
        '/CN=example.com'
        >>> format_name([('CN', 'example.com'), ('O', "My Organization"), ])
        '/CN=example.com/O=My Organization'
    """
    if isinstance(subject, x509.Name):
        subject = [(OID_NAME_MAPPINGS[s.oid], s.value) for s in subject]

    return '/%s' % ('/'.join(['%s=%s' % (k, v) for k, v in subject]))


def format_general_name(name):
    """Format a single general name.

    >>> import ipaddress
    >>> format_general_name(x509.DNSName('example.com'))
    'DNS:example.com'
    >>> format_general_name(x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')))
    'IP:127.0.0.1'
    """

    if isinstance(name, x509.DirectoryName):
        value = format_name(name.value)
    else:
        value = name.value
    return '%s:%s' % (SAN_NAME_MAPPINGS[type(name)], value)


def add_colons(s):
    """Add colons after every second digit.

    This function is used in functions to prettify serials.

    >>> add_colons('teststring')
    'te:st:st:ri:ng'
    """
    return ':'.join([s[i:i + 2] for i in range(0, len(s), 2)])


def int_to_hex(i):
    """Create a hex-representation of the given serial.

    >>> int_to_hex(12345678)
    'BC:61:4E'
    """
    s = hex(i)[2:].upper()
    return add_colons(s)
