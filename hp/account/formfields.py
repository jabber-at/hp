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

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator

from bootstrap.formfields import BootstrapMixin

from .widgets import DomainWidget
from .widgets import NodeWidget
from .widgets import UsernameWidget

_MIN_USERNAME_LENGTH = getattr(settings, 'MIN_USERNAME_LENGTH', 2)
_MAX_USERNAME_LENGTH = getattr(settings, 'MAX_USERNAME_LENGTH', 64)


class UsernameField(BootstrapMixin, forms.MultiValueField):
    def __init__(self, **kwargs):
        self.register = kwargs.pop('register', False)
        self.status_check = kwargs.pop('status_check', self.register)

        hosts = getattr(settings, 'XMPP_HOSTS', {})
        if self.register is True:
            hosts = [k for k, v in hosts.items()
                     if v.get('REGISTRATION') and v.get('MANAGE', True)]
        else:
            hosts = [k for k, v in hosts.items() if v.get('MANAGE', True)]
        choices = tuple([(d, '@%s' % d) for d in hosts])

        # Add a CSS class to the formgroup
        kwargs.setdefault('formgroup_attrs', {})
        if kwargs['formgroup_attrs'].get('class'):
            kwargs['formgroup_attrs']['class'] += ' form-inline'
        else:
            kwargs['formgroup_attrs']['class'] = 'form-inline'

        fields = (
            forms.CharField(
                widget=NodeWidget,
                min_length=_MIN_USERNAME_LENGTH,
                max_length=_MAX_USERNAME_LENGTH,
                error_messages = {
                    'min_length': _('Username must have at least %(limit_value)d characters.'),
                    'max_length': _('Username must have at most %(limit_value)d characters.'),
                },
                validators=[
                    RegexValidator(r'^[^@\s]+$', _('Username contains invalid characters.')),
                ],
            ),
            forms.ChoiceField(initial=settings.DEFAULT_XMPP_HOST, choices=choices,
                              disabled=len(hosts) == 1, widget=DomainWidget),
        )
        widgets = [f.widget for f in fields]

        attrs = {}
        if self.register is True:
            attrs['class'] = 'status-check'
        self.widget = UsernameWidget(widgets=widgets, attrs=attrs)
        super(UsernameField, self).__init__(fields=fields, require_all_fields=True, **kwargs)

    def compress(self, data_list):
        node, domain = data_list
        return '@'.join(data_list)
