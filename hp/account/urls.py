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

from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import forms
from . import views


app_name = 'account'
urlpatterns = [
    url(r'register/$', views.RegisterUserView.as_view(), name='register'),
    url(r'login/$', auth_views.login, {
            'template_name': 'account/user_login.html',
            'authentication_form': forms.LoginForm,
        }, name='login'),
    url(r'logout/$', auth_views.logout, name='logout'),
    url(r'$', views.UserView.as_view(), name='detail'),
]
