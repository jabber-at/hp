# Example localsettings.py file for this project.
#
# List of all stock Django settings:
#       https://docs.djangoproject.com/en/1.10/ref/settings/
#
# Mandatory settings from Django: SECRET_KEY, STATIC_ROOT, MEDIA_ROOT, DEFAULT_FROM_EMAIL
# Mandatory settings used by this HP: XMPP_HOSTS, CONTACT_ADDRESS, DEFAULT_XMPP_HOST

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

###############################
# Normal Django configuration #
###############################

# Database configuration
# See also: https://docs.djangoproject.com/en/1.10/ref/databases/

# Admins that get tracebacks
#ADMINS = (
#    ('Firstname Lastname', 'user@example.com'),
#)

# Hostnames that this page runs under
# Note that if not set, the hostnames from XMPP_HOSTS will be used.
#ALLOWED_HOSTS = (
#    'example.com', 'www.example.com',
#)

# Static and media files configuration
#MEDIA_ROOT = '/var/www/example.com/media/'
#MEDIA_URL = '/media/'
STATIC_ROOT = '/var/www/hp/static/'

# Set this to True during development
#DEBUG = False
#SECRET_KEY = 'dummy'

# If you want to configure INSTALLED_APPS to add your own Django apps, you can either completely
# override the INSTALLED_APPS setting or set it to a callable that will receive the default value
# must return your modified value. For more information, see:
#     https://jabber.at/doc/settings.html#setting-installed-apps
#INSTALLED_APPS = [...]

# If you add additional apps via INSTALLED_APPS and want to add more routes, you can do so here.
# Djangos "path()" function is described here:
#   https://docs.djangoproject.com/en/2.0/ref/urls/#path
#ADDITIONAL_URL_PATHS = [
#   # This will be added as path('your-path/', include('your_django_app.urls')):
#   ('your-path/', 'your_django_app.urls'),
#]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'db',
        # NOTE: other variables are set via env variables
    }
}

#########################
# General configuration #
#########################

# The copyright notice at the bottom of the page. "%(year)s is replaced with the current year, and
# "%(brand)s" is replaced with the "BRAND" key of the current site.
#COPYRIGHT_NOTICE = _('© 2010-%(year)s, %(brand)s.')

# Location of the admin interface
#ADMIN_URL = 'admin/'

# You can define a different root directory for uploaded images via the admin interface. This is
# useful if your MEDIA_URL is on a separate domain (e.g. because XEP-0363 uploads should be served
# from somewhere else) and still want your own uploaded files saved to a different directory.
#BLOG_MEDIA_ROOT = '/var/www/other.example.com/media/'
#BLOG_MEDIA_URL = '/media/'

# You can configure the panels shown in the left sidebar. To add your own panels, you need to add
# your own app via INSTALLED_APPS above and then give paths inside the "templates" directory of
# your app. The default is shown below.
#SIDEBAR_PANELS = [
#    'core/cards/languages.html',
#    # tools is not enabled by default, requires some third-party apps
#    #'core/cards/tools.html',
#    'core/cards/updates.html',
#]

###########
# Content #
###########
# You can configure a few pages here that if configured will appear in a few templates where
# appropriate. Values can either be an integer, in which case it's the primary key of the database
# object, or a str for a slug of the page. The primary key is preferred because the lookup is
# faster and link URLs will be internationalized. You can get the primary key from the URL in the
# admin interface (e.g. /admin/blog/page/<pk>/).

# A page containing client recommondations
#CLIENTS_PAGE = 3

# A page containing "Frequently asked questions"
#FAQ_PAGE = 5

#########################
# Account configuration #
#########################

# Minimum and maximum username length allowed by the interface.
#MIN_USERNAME_LENGTH = 2
#MAX_USERNAME_LENGTH = 64

# Require a unique email address. By default an address can be used by multiple accounts.
#REQUIRE_UNIQUE_EMAIL = True

# If your XMPP server automatically removes unused accounts (e.g. via
# "ejabberdctl delete_old_users", the project supports sending emails to users that their account
# is about to be removed.
#
# NOTE: The project NEVER automatically removes accounts from the XMPP server. The settings here
#       only configure the warning messages to users.
#
# Accounts are automatically removed after this many days. If None (the default), accounts are not
# automatically removed.
#ACCOUNT_EXPIRES_DAYS = 365

# Notify users after this many days of inactivity about pending account removal. The default is
# seven days before ACCOUNT_EXPIRES_DAYS.
#ACCOUNT_EXPIRES_NOTIFICATION_DAYS = 358

# You can configure the user menu (visible on all /account pages to disable or even add
# functionality. This can be a list of tuples replacing the initial value, or a callable
# that manipulates the default value. For more information, please see:
#   https://jabber.at/doc/settings.html
#ACCOUNT_USER_MENU = [... ]

##########
# Caches #
##########
# See also: https://docs.djangoproject.com/en/dev/topics/cache/

# Django uses an in-memory cache by default. In development, it's recommended you use a persistent
# cache because the xmpp_backends.dummy.DummyBackend uses Djangos cache.
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

##################
# Email settings #
##################

# Email settings (see Django docs for all options)
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = ''
#EMAIL_PORT = 587
#EMAIL_HOST_USER = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = True

###########
# Logging #
###########

# The log format used. Note that Celery also has more specific settings below.
#LOG_FORMAT = '[%(asctime).19s %(levelname)-8s] %(message)s' # .19s = only first 19 chars

# Log level used for our own code
#LOG_LEVEL = 'INFO'

# Log level used for any library code
#LIBRARY_LOG_LEVEL = 'WARN'

############################
# XMPP hosts configuration #
############################

# Connection to the XMPP server. For more information, see:
#    http://xmpp-backends.readthedocs.io/en/latest/
XMPP_BACKENDS = {
    'default': {
        # For development, uses Djangos cache (see CACHES)
        #'BACKEND': 'xmpp_backends.dummy.DummyBackend',

        # A sample connection using xmlrpc
        #'BACKEND': 'xmpp_backends.ejabberd_xmlrpc.EjabberdXMLRPCBackend',
        #'uri': 'https://...',
        #'user': 'user',
        #'server': 'example.com',
        #'password': '...',
    },
}

# Hosts handled by this domain (used in registration form etc.)
XMPP_HOSTS = {
    'example.com': {
        'ALLOWED_HOSTS': ['example.com']
    },
}

# Default address the contact form sends emails to.
CONTACT_ADDRESS = 'contact@example.com'

# If set, the contact form will name this MUC as primary contact address.
#CONTACT_MUC = 'chat@conference.example.com'

# Default email used when a host in XMPP_HOSTS does not define one.
DEFAULT_FROM_EMAIL = 'noreply@example.com'

# The default host used on this site. This affects the default selection in some <select> HTML form
# elements, as well as for content that should be the same accross all hosts, e.g. the canonical
# URL of a blog post.
DEFAULT_XMPP_HOST = 'example.com'

################
# Social media #
################
# Various social media accounts
#FACEBOOK_PAGE = 'example.com'
#TWITTER_HANDLE = 'example_com'

# You can (and should) customize social media texts for static pages. This is a dictionary of view
# names and you can set the keys "meta_desc", "twitter_title", "twitter_desc", "og_title" and
# "og_desc" for every named view.
#SOCIAL_MEDIA_TEXTS = {
#   'blog:home': {
#       'meta_desc': _('Start page description (will show up on e.g. Google)'),
#   }
#}

###########
# Webchat #
###########
# See https://conversejs.org/docs/html/configuration.html for available configuration variables
#CONVERSEJS_CONFIG = {
#    'bosh_service_url': 'https://example.com/http-bind/',
#    'show_controlbox_by_default': True,
#    'roster_groups': True,
#    'allow_registration': False,
#}

# You can also define a setup callback, which is a javascript function that will receive
# CONVERSEJS_CONFIG as only parameter. You must take care of initializing everything yourself!
#CONVERSEJS_SETUP_CALLBACK = 'init_conversejs'

########################
# Celery configuration #
########################
# See also: http://docs.celeryproject.org/en/latest/configuration.html

CELERY_BROKER_URL = 'redis://cache:6379/0'

# The log format used by the celery loggers. If None (the default), the same as LOG_FORMAT will be
# used.
#CELERY_WORKER_LOG_FORMAT = None

# The format used for Celery task loggers (-> get_task_logger()). The default is the same as the
# normal default, except that the task name is added.
#CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime).19s %(levelname)-8s] [%(task_name)s] %(message)s'

######################
# Anti-Spam settings #
######################

# CAPTCHAs
#
#ENABLE_CAPTCHAS = True
#CAPTCHA_LENGTH = 8
#CAPTCHA_FONT_SIZE = 32

# DNS-based Blackhole List
# IPs that are on one of these DNSBLs are not allowed to use views that use core.views.DnsBlMixin.
#
#DNSBL = (
#    'sbl.spamhaus.org',
#    'xbl.spamhaus.org',
#    'proxies.dnsbl.sorbs.net',
#    'spam.abuse.ch',
#    'cbl.abuseat.org',
#)
DNSBL = ()

# When you block accounts via the admin interface, their email address is also blocked.
# If the account has had recent activity known (e.g. changed password, ...) the IP
# address is also blocked. By default, email addresses are blocked indefinetly, while
# IP addresses are blocked for a 31 days after their last activity for that account.
#BLOCKED_EMAIL_TIMEOUT = None
#BLOCKED_IPADDRESS_TIMEOUT = timedelta(days=31)


# A manually maintained list of IP addresses or networks that are blocked. Used by the
# BlocklistMixin.
#SPAM_BLACKLIST = {
#    '192.0.2.0',  # You can use IP addresses...
#    '192.0.0.0/28',  # ... or network ranges
#}

# Ratelimits
# Enforce a rate limit per IP for views that use core.views.RateLimitMixin. Use one of the
# constants in core.constants.ACTIVITY_*.
#
#RATELIMIT_CONFIG = {
#    ACTIVITY_REGISTER: (
#        (timedelta(hours=1), 5, ),
#    ),
#    ACTIVITY_FAILED_LOGIN: (
#        (timedelta(minutes=30), 3, ),
#    ),
#}

# Domains that cannot be used for registration because they are used for SPAM
#BANNED_EMAIL_DOMAINS = {'spam.com', 'spam.net', }

# Do not allow registrations using email addresses matching any of the given regular expressions.
# If you just want to match a specific domain, please use BANNED_EMAIL_DOMAINS instead, it will
# display a more specific error message and the check is a lot faster.
#EMAIL_BLACKLIST = (
#    re.compile('^[a-z]@'),  # one-letter email addresses are mean for some reason ;-)
#)

# If set, only allow registrations if the users email address matches any of the listed regular
# expressions. Note that BANNED_EMAIL_DOMAINS and EMAIL_BLACKLIST is checked first.
#EMAIL_WHITELIST = (
#    re.compile('@example\.com$'),
#    re.compile('@example\.net$'),
#)

#####################
# GPG configuration #
#####################

# GPG keyserver used for fetching keys
#GPG_KEYSERVER = 'http://pool.sks-keyservers.net:11371'

# Location of the *private* key files used for signing GPG emails. This directory is expected
# to contain the private keys configured in the GPG_FINGERPRINT setting in XMPP_HOSTS. The name
# of the files should be <fingerprint>.key.
#GPG_KEYDIR = ''

# Custom GPG backend.
# NOTE: The backend here is never used verbatim in production. All public keys for users come from
#       the database, private keys come from the filesystem (see GPG_KEYDIR). Every GPG operation
#       is done in a separate keyring that is deleted after use. This is done to (a) isolate users
#       from each other and (b) because of various threading issues with GPG.
#
#GPG_BACKENDS = {
#    'default': {
#        'BACKEND': 'gpgliblib.gpgme.GpgMeBackend',
#        'HOME': os.path.join(ROOT_DIR, 'gnupg'),
#        # Optional settings:
#        'PATH': '/home/...',  # Path to 'gpg' binary
#        'ALWAYS_TRUST': True,   # Ignore trust in all operations
#        'OPTIONS': {...},  # Any custom options for the specific backend implementation
#    },
#}

####################
# Privacy settings #
####################

# When UserLogEntry records are deleted. These are log entries in the "Recent activity" tab of
# the user.
#USER_LOGENTRY_EXPIRES = timedelta(days=31)

##############################
# XEP-0363: HTTP File Upload #
##############################
# See also: https://github.com/mathiasertl/django-xmpp-http-upload

XMPP_HTTP_UPLOAD_ACCESS = (
    # This user has no limits
    (r'^user@example\.com$', {}),
    # Users on these domains have more explicit limits
    ([r'@example\.com$', r'@example\.net$', ], {
        # User may not upload a file larger then 30MB:
        'max_file_size': 30 * 1024 * 1024,

        # User may not upload more then 150 MB in total
        'max_total_size': 150 * 1024 * 1024,

        # User may not upload more then 50 MB per hour
        'bytes_per_timedelta': {
            'delta': timedelta(hours=1),
            'bytes': 100 * 1024 * 1024,
        },

        # User may not do more then ten uploads per hour
        'uploads_per_timedelta': {
            'delta': timedelta(hours=1),
            'uploads': 10,
        },
    }),
)

# How long files are shared before they are deleted:
#XMPP_HTTP_UPLOAD_SHARE_TIMEOUT = 86400 * 31

# Top-level domain to use
#XMPP_HTTP_UPLOAD_URL_BASE = 'https://jabber.at'

# Django stores larger uploads as temporary files. This means that on many systems, those files
# will not be world-readable by default. You can overwrite the default permissions for uploaded
# files. See also:
#   https://docs.djangoproject.com/en/1.11/topics/http/file-uploads/#upload-handlers
#   https://docs.djangoproject.com/en/1.11/ref/settings/#file-upload-permissions
#   https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-FILE_UPLOAD_MAX_MEMORY_SIZE
#FILE_UPLOAD_PERMISSIONS = 0o644

###########
# VARIOUS #
###########
# By default, the Celery worker will download TLS badges for all hosts configured in XMPP_HOSTS
# from the XSF IM Observatory. The badges will be available at MEDIA_URL/badge_<host>.svg, e.g.
# https://jabber.at/media/badge_jabber_at.svg. The use of this is to be able to display current
# badges with strict CSP headers in place.
#
# The current default is check.messaging.one, but will switch back to xmpp.net if they ever manage
# to provide a service to the community again. You can set this to None to completely disable
# fetching these badges.
#OBSERVATORY_URL = 'https://check.messaging.one'
