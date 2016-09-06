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


class AddressQuerySet(models.QuerySet):
    def count_activities(self):
        return self.annotate(count_activities=models.Count('addressactivity', distinct=True))

    def count_confirmations(self):
        return self.annotate(count_confirmations=models.Count('confirmations', distinct=True))

    def first_activity(self):
        return self.annotate(first_activity=models.Min('addressactivity__timestamp'))

    def last_activity(self):
        return self.annotate(last_activity=models.Max('addressactivity__timestamp'))


class AddressActivityQuerySet(models.QuerySet):
    pass
