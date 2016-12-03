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
# If not, see <http://www.gnu.org/licenses/.

from django import forms
from django.utils.translation import gettext_lazy as _

_meta_help = _('For search engines. Max. 160 characters, '
               '<span class="test-length">160</span> left.')
_twitter_help = _('At most 200 characters, <span class="test-length">200</span> left.')


class BasePageAdminForm(forms.ModelForm):
    class Meta:
        # TODO: dynamically adapt to enabled langs?
        help_texts = {
            'meta_summary_de': _meta_help,
            'meta_summary_en': _meta_help,
            'twitter_summary_de': _twitter_help,
            'twitter_summary_en': _twitter_help,
        }
