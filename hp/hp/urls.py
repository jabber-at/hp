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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('%s/uwsgi/' % settings.ADMIN_URL.strip('/'), include('django_uwsgi.urls')),
    path(settings.ADMIN_URL.lstrip('/'), admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('captcha/', include('captcha.urls')),

    path('account/', include('account.urls')),
    path('feed/', include('feed.urls')),
    path('chat/', include('conversejs.urls')),
    path('certs/', include('certs.urls')),
    path('xep0363/', include('xmpp_http_upload.urls')),
    path('', include('core.urls')),
]

for route, module in settings.ADDITIONAL_URL_PATHS:
    urlpatterns.append(path('', include(module)))

# This is catch-all
urlpatterns.append(path('', include('blog.urls')))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'ENABLE_DEBUG_TOOLBAR', False) is True:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
