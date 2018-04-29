from email.utils import parseaddr

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class CoreConfig(AppConfig):
    name = 'core'

    def _test_email(self, addr, msg=''):
        if parseaddr(addr) == ('', ''):
            msg = msg or ('"%s" is not a valid email address' % addr)
            raise ImproperlyConfigured(msg)

    def ready(self):
        super().ready()

        # Test some settings for validity. This is better then testing in settings.py
        # because the settings module can be overwritten (and is overwritten in the test suite).
        self._test_email(settings.CONTACT_ADDRESS)
