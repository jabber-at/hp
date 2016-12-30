########
Settings
########

In general, as a `Django <https://www.djangoproject.com/>`_ project, this project is configured
like any other project, in a file called :file:`settings.py`, located at ``hp/hp/settings.py``.
Please see Djangos documentation on `how settings work
<https://docs.djangoproject.com/en/dev/topics/settings/>`_ and the `complete settings reference
<https://docs.djangoproject.com/en/dev/ref/settings/>`_ of all settings supported by Django. This
project of course uses a few additional settings to make it more configurable.

To make the project more reusable, :file:`settings.py` includes a file :file:`localsettings.py` in
the same folder, if it is present. :file:`localsettings.py` is ignored in git, so you don't have to
maintain a separate branch or anything if you run your own copy. There is a file called
:file:`localsettings.py.example` that you can copy in order to get you started.

**************
Stock settings
**************

Some stock Django settings deserve a few additional notes.

.. _setting-installed_apps:

INSTALLED_APPS
==============

If you set ``INSTALLED_APPS`` to a callable in :file:`localsettings.py`, that callable will be
called with the default value of ``INSTALLED_APPS``, the callable should return the list of the
real value. This is useful if you want to add your own apps but do not want repeat all the default
apps included in the project (which might change without notice).

For example, if you want to add your own ``skin`` app as first app (which could e.g. override
templates or static files), you could do::

   def INSTALLED_APPS(apps):
       apps.insert(0, 'skins')
       return apps

****************
Project settings
****************

Project settings are settings used by this project and are not native to Django. Most are
documented in :file:`localsettings.py.example`.

.. WARNING::

   This section is very incomplete. Currently, :file:`localsettings.py.example` should be
   considered the authoritative source.


.. _setting-account_expires_days:

ACCOUNT_EXPIRES_DAYS
====================

Default: ``None``

.. _setting-account_expires_notification_days:

ACCOUNT_EXPIRES_NOTIFICATION_DAYS
=================================

Default: :ref:`setting-account_expires_days` minus seven days

.. _setting-account_user_menu:

ACCOUNT_USER_MENU
=================

Default: (please see :file:`settings.py`)

Configure the user menu displayed on all pages under /account, if the user is logged in. Just like
with :ref:`setting-installed_apps`, you can either override the default value by setting a list or
extend the default value by setting a callable.

The value is a list of two-tuples, the first being a resolvable URL name (with no arguments) and
the second being a config dictionary::

   ACCOUNT_USER_MENU = [
       ('account:detail', {
           # Title displayed in the menu
           'title': _('Overview'),

           # If False, the item is also displayed if the user does not (yet) have a confirmed
           # email address. The default is True.
           'requires_confirmation': False,
       }),
       #...

.. _setting-admin_url:

ADMIN_URL
=========

Default: ``"/admin/"``

The location of the admin interface, the default is ``"/admin/"``.

.. _setting-max_username_length:

MAX_USERNAME_LENGTH
===================

Default: ``64``

The maximum length for usernames when a user registers. This limit is only enforced on the main
webpage (at /account/register/). Users with longer usernames can still be created via the admin
interface, via the command line or via some import from the XMPP server.

Existing users with longer usernames don't have any reduced functionality, they can still e.g.
reset their password.

.. _setting-min_username_length:

MIN_USERNAME_LENGTH
===================

Default: ``2``

See :ref:`setting-min_username_length`.

.. _setting-require_unique_email:

REQUIRE_UNIQUE_EMAIL
====================

Default: ``False``

Set to ``True`` to require users to use a unique email address. By default, users can use the same
email address for multiple accounts.

SOCIAL_MEDIA_TEXTS
==================

.. TODO:: List all possible social media texts to override.

XMPP_BACKENDS
=============

This setting configures the backend used to communicate with your XMPP server. Please see
the `xmpp-backends library <http://xmpp-backends.readthedocs.io/en/latest/>`_ for more information.
