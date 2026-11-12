# -*- coding: utf-8 -*-
#
# This file is part of the jabber.at homepage (https://github.com/jabber-at/hp).
#
# This project is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along with this project. If not, see
# <http://www.gnu.org/licenses/>.

from django.urls import re_path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'account'
urlpatterns = [
    re_path(r'^register/$', views.RegistrationView.as_view(), name='register'),
    re_path(r'^register/(?P<key>\w+)/$', views.ConfirmRegistrationView.as_view(),
        name='register_confirm'),
    re_path(r'^login/$', views.LoginView.as_view(), name='login'),
    re_path(r'^sessions/$', views.SessionsView.as_view(), name='sessions'),
    re_path(r'^notifications/$', views.NotificationsView.as_view(), name='notifications'),
    re_path(r'^password/$', views.SetPasswordView.as_view(), name='set_password'),
    re_path(r'^password/reset/$', views.ResetPasswordView.as_view(), name='reset_password'),
    re_path(r'^password/reset/(?P<key>\w+)/$', views.ConfirmResetPasswordView.as_view(),
        name='reset_password_confirm'),
    re_path(r'^email/$', views.SetEmailView.as_view(), name='set_email'),
    re_path(r'^email/(?P<key>\w+)/$', views.ConfirmSetEmailView.as_view(), name='set_email_confirm'),
    re_path(r'^uploads/$', views.HttpUploadView.as_view(), name='xep0363'),
    re_path(r'^gpg/$', views.GpgView.as_view(), name='gpg'),
    re_path(r'^gpg/(?P<pk>\d+)/$', views.ManageGpgView.as_view(), name='manage_gpg'),
    re_path(r'^gpg/add/$', views.AddGpgView.as_view(), name='add_gpg'),
    re_path(r'^log/$', views.RecentActivityView.as_view(), name='log'),
    re_path(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    re_path(r'^api/check-user/$', views.UserAvailableView.as_view(), name='api-check-user'),
    re_path(r'^api/xep0363/(?P<pk>\d+)/$', views.DeleteHttpUploadView.as_view(),
        name='api-xep0363-delete'),
    re_path(r'^api/sessions/(?P<resource>.+)/$$', views.StopUserSessionView.as_view(),
        name='api-stop-user-session'),
    re_path(r'^delete/$', views.DeleteAccountView.as_view(), name='delete'),
    re_path(r'^delete/(?P<key>\w+)/$', views.ConfirmDeleteAccountView.as_view(),
        name='delete_confirm'),
    re_path(r'^$', views.UserView.as_view(), name='detail'),
]
