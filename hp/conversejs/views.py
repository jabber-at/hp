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

import json

from django.conf import settings
from django.http import HttpResponse
from django.views.generic.base import TemplateView


class ConverseJsView(TemplateView):
    template_name = 'conversejs/main.html'


class ConverseJsInitView(TemplateView):
    template_name = 'conversejs/init.js'

    def get_context_data(self, *args, **kwargs):
        ctx = super(ConverseJsInitView, self).get_context_data(*args, **kwargs)
        ctx['config'] = json.dumps(settings.CONVERSEJS_CONFIG)
        ctx['setup_callback'] = settings.CONVERSEJS_SETUP_CALLBACK
        return ctx

    def _get(self, request):
        js = ''
        if settings.CONVERSEJS_CONFIG:
            js = 'converse.initialize(%s);' % json.dumps(settings.CONVERSEJS_CONFIG)
        return HttpResponse(js, content_type='application/javascript')
