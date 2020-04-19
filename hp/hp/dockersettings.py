# Example localsettings.py file for this project.
#
# List of all stock Django settings:
#       https://docs.djangoproject.com/en/1.10/ref/settings/
#
# Mandatory settings from Django: SECRET_KEY, STATIC_ROOT, MEDIA_ROOT, DEFAULT_FROM_EMAIL
# Mandatory settings used by this HP: XMPP_HOSTS, CONTACT_ADDRESS, DEFAULT_XMPP_HOST

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = '/var/www/hp/static/'
DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'db',
        # NOTE: other variables are set via env variables
    }
}

##########
# Caches #
##########
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://cache:6379/1",

        # Use this in development, that way users don't disappear from the "backend" (which is just
        # this redis cache).
        #"TIMEOUT": None,  # never expire
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

CELERY_BROKER_URL = 'redis://cache:6379/0'
