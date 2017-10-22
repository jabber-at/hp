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


from xmlrpc import client


class FastFailTransport(client.Transport):
    """This class sole purpose is to set a timeout of 10 seconds."""

    def make_connection(self, *args, **kwargs):
        # supperclass returns http.client.HttpConnection
        conn = super(FastFailTransport, self).make_connection(*args, **kwargs)

        # override the timeout
        conn.timeout = 10
        return conn
