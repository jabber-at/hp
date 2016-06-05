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

from django.contrib.auth.models import BaseUserManager

from .constants import REGISTRATION_MANUAL

class UserManager(BaseUserManager):
    def create_superuser(self, jid, email, password, method=None):
        if method is None:
            method = REGISTRATION_MANUAL

        user = self.model(jid=jid, email=email, registration_method=method,
                          is_superuser=True)
        user.save(using=self.db)
        return user
