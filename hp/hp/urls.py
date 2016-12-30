"""hp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin

from core.urlpatterns import i18n_url

urlpatterns = [
    url(r'^%s/' % settings.ADMIN_URL.strip('/'), admin.site.urls),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^captcha/', include('captcha.urls')),

    url(r'^account/', include('account.urls')),
    url(r'^feed/', include('feed.urls')),
    url(r'^conversejs/', include('conversejs.urls')),
    url(r'^xep0363/', include('xmpp_http_upload.urls', namespace='xmpp-http-upload')),
    i18n_url(r'^', include('core.urls')),
    url(r'^', include('blog.urls')),
]
