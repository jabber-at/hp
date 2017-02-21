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


def stat(metric, value):
    """Just a shortcut."""
    return Event.objects.create(metric=metric, value=value)


class Event(models.Model):
    stamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metric = models.CharField(max_length=32, db_index=True)
    value = models.IntegerField()

    def __str__(self):
        return '%s: %s' % (self.metric, self.value)
