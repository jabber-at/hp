###########
Development
###########

*************
Initial setup
*************

The python libraries have some dependencies, on Debian/Ubuntu, install them
with::

   apt-get install python3-dev libgpgme11-dev

To start, clone the project and initialize the virtualenv::

   git clone https://github.com/jabber-at/hp
   cd hp
   virtualenv -p /usr/bin/python3 .
   pip install -U pip setuptools
   pip install -r requirements.txt -r reqirements-dev.txt
   cd hp
   python manage.py migrate

Configuration
=============

There is a file called ``hp/hp/localsettings.py.example``. Adapt it to your needs.

Note that you can configure Django to send emails to stdout instead via SMTP::

   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

***********************
Run the project locally
***********************

To run the testserver, use::

   python manage.py runserver

To run the Celery daemon (which is needed for sending emails etc.), use (in the same dir as
``manage.py``)::

   celery -A hp worker -l info -B

**************************
Build/upload documentation
**************************

To build documentation, simply do (from the root directory)::

   make -C doc html

To upload documentation to https://jabber.at/doc, simply do::

   fab upload_doc

Note that this requires a correctly configured :file:`fab.conf`, see :doc:`deployment`.


******************
Naming conventions
******************

Variable names
==============

Some variable names are used accross the project to denote a specific thing. This makes the code
more readable for developers.

.. NOTE:: This is still applied very inconsistently.

================= ================================================================================
Variable          Meaning
================= ================================================================================
user              A :py:class:`account.models.User` instance.
hostname          The name of a host configured in the ``XMPP_HOSTS`` setting.
host              A configuration for a specific host, e.g. ``settings.XMPP_HOSTS[hostname]``.
{...}_pk          The ``_pk`` suffix means this is an integer representing the database primary key
                  of a database instance, e.g. ``user = User.objects.get(pk=user_pk)``.
sign_{fp,key,pub} A fingerprint, private or public key used for signing a message.
recv_{fp,key,pub} A fingerprint, private or public key used for encrypting a message.
================= ================================================================================

Interface text
==============

We try to use consistent spelling with some keywords in the interface. E.g. it doesn't look good if
you use ``Email`` on one page and then ``e-mail`` on the next page.

============= =============== ====================================================================
Spelling      German          Description
============= =============== ====================================================================
Jabber        Jabber          "We are a *Jabber* server.
email         E-Mail          "We sent you an *email*."
email address E-Mail-Addresse "Enter a valid *email address*."
account       Konto           "Create an *account*."
client        Client          "Use a *client* to connect to jabber.at."
user          BenutzerIn      "A *user* needs to...."
users         BenutzerInnen   "*Users* are required to..."
============= =============== ====================================================================

.. seealso::

   Django also has some similar standard:

   https://docs.djangoproject.com/en/dev/internals/contributing/writing-documentation/#commonly-used-terms

The website addresses a user as "you", in German, we use the polite form in lower case:

* English: "Please make sure you know what you're doing."
* German: "Bitte seien sie sich sicher, was sie tun."

*******
Testing
*******

For the testsuite, you need to download the `geckodriver binary
<https://github.com/mozilla/geckodriver/releases>`_ to ``contrib/selenium``:

After the, running the test-suite is as simple as::

   fab check
   fab test
