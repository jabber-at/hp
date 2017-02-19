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

from . import views


app_name = 'account'
urlpatterns = [
    url(r'^register/$', views.RegistrationView.as_view(), name='register'),
    url(r'^register/(?P<key>\w+)/$', views.ConfirmRegistrationView.as_view(),
        name='register_confirm'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^sessions/$', views.SessionsView.as_view(), name='sessions'),
    url(r'^notifications/$', views.NotificationsView.as_view(), name='notifications'),
    url(r'^password/$', views.SetPasswordView.as_view(), name='set_password'),
    url(r'^password/reset/$', views.ResetPasswordView.as_view(), name='reset_password'),
    url(r'^password/reset/(?P<key>\w+)/$', views.ConfirmResetPasswordView.as_view(),
        name='reset_password_confirm'),
    url(r'^email/$', views.SetEmailView.as_view(), name='set_email'),
    url(r'^email/(?P<key>\w+)/$', views.ConfirmSetEmailView.as_view(), name='set_email_confirm'),
    url(r'^uploads/$', views.HttpUploadView.as_view(), name='xep0363'),
    url(r'^gpg/$', views.GpgView.as_view(), name='gpg'),
    url(r'^gpg/(?P<pk>\d+)/$', views.ManageGpgView.as_view(), name='manage_gpg'),
    url(r'^gpg/add/$', views.AddGpgView.as_view(), name='add_gpg'),
    url(r'^log/$', views.RecentActivityView.as_view(), name='log'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^api/check-user/$', views.UserAvailableView.as_view(), name='api-check-user'),
    url(r'^api/xep0363/(?P<pk>\d+)/$', views.DeleteHttpUploadView.as_view(),
        name='api-xep0363-delete'),
    url(r'^api/sessions/(?P<resource>.+)/$$', views.StopUserSessionView.as_view(),
        name='api-stop-user-session'),
    url(r'^delete/$', views.DeleteAccountView.as_view(), name='delete'),
    url(r'^delete/(?P<key>\w+)/$', views.ConfirmDeleteAccountView.as_view(),
        name='delete_confirm'),
    url(r'^$', views.UserView.as_view(), name='detail'),
]
