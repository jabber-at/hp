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

from django.conf import settings
from django.db import models

from basedjango.models import BaseModel

#from composite_field.l10n import LocalizedCharField
#from composite_field.l10n import LocalizedTextField
from core.modelfields import LocalizedCharField
from core.modelfields import LocalizedTextField


class BlogPost(BaseModel):
    title = LocalizedCharField(max_length=16)
    text = LocalizedTextField()

    author = models.ForeignKey(settings.AUTH_USER_MODEL)
