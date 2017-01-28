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

from django.utils.translation import ugettext_lazy as _


REGISTRATION_WEBSITE = 0
REGISTRATION_INBAND = 1
REGISTRATION_MANUAL = 2
REGISTRATION_UNKNOWN = 9
REGISTRATION_CHOICES = (
    (REGISTRATION_WEBSITE, _('Via Website')),
    (REGISTRATION_INBAND, _('In-Band Registration')),
    (REGISTRATION_MANUAL, _('Manually')),
    (REGISTRATION_UNKNOWN, _('Unknown')),
)

TARGET_URL = 0
TARGET_NAMED_URL = 1
TARGET_MODEL = 2
TARGET_CHOICES = {
    TARGET_URL: _('URL'),
    TARGET_NAMED_URL: _('URL Name'),
    TARGET_MODEL: _('Model'),
}

# Logged user activities
ACTIVITY_REGISTER = 0
ACTIVITY_RESET_PASSWORD = 1
ACTIVITY_SET_PASSWORD = 2
ACTIVITY_SET_EMAIL = 3
ACTIVITY_FAILED_LOGIN = 4
ACTIVITY_CONTACT = 5  # used for ratelimiting
