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

SOCIAL_MEDIA_TEXTS
==================

.. TODO:: List all possible social media texts to override.

XMPP_BACKENDS
=============

This setting configures the backend used to communicate with your XMPP server. Please see
the `xmpp-backends library <http://xmpp-backends.readthedocs.io/en/latest/>`_ for more information.
