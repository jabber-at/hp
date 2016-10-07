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
# If not, see <http://www.gnu.org/licenses/>.

from django.db import models

_LOGGED_HEADERS = {
    'CONTENT_LENGTH',
    'CONTENT_TYPE',
    'REMOTE_ADDR',
    'REQUEST_METHOD',
}


class AddressManager(models.Manager):
    pass


class AddressActivityManager(models.Manager):
    def log(self, request, activity, note='', user=None):
        user = user or request.user
        Address = self.model._meta.get_field('address').rel.to
        address = Address.objects.get_or_create(address=request.META['REMOTE_ADDR'])[0]
        headers = {k: v for k, v in request.META.items()
                   if k in _LOGGED_HEADERS or k.startswith('HTTP_')}

        return self.create(address=address, user=user, activity=activity, note=note,
                           headers=headers)
