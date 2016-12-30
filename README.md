This repository hosts the code for our homepage at https://jabber.at.

The homepage is still an evolving project, with many features unifinished, maybe buggy, etc.

### Requirements

* Python 3.4+, Django 1.10+
* A webserver and a database (anything that works with Django)
* An XMPP-server, this project interfaces with it via
  [xmpp-backends](https://github.com/mathiasertl/xmpp-backends).

### Features

* A pretty standard blog including static pages.
* Vary some behavior depending on the hostname used, e.g. a different logo on example.com,
  example.net and example.zone.
* A contact page, with GPG encryption if the user added keys.
* Verious tasks are performed asynchronously using a Celery worker. This adds fast response times
  even if an operation takes a while (e.g. fetching keys, keyservers are notoriously slow) and
  dynamic retries (e.g. fetching keys, keyservers are notoriously unreliable).

#### User management

* Registration and password reset for XMPP users directly on the homepage.
* Authentication is performed against the XMPP server, the password is never stored locally.
* Users can add GPG keys to encrypt emails (password reset, ...) with GPG.
* Manage XEP-0363 uploads.

### Documentation

The documentation is located at https://jabber.at/doc.

### ChangeLog

See [ChangeLog.md](https://github.com/jabber-at/hp/blob/master/Changelog.md)

### TODOs

* Tags and comments on blog posts.
* Add a webclient again (JSXC or converse.js?).
* Calendar export of scheduled downtimes.
* Minimize Javascript and CSS.
* Search functionality.

#### Ideas

These are a bit further down the road.

1. Some account settings integration (e.g. ability to configure MAM settings)
2. Security stuff (e.g. from where you logged in recently, ...)
3. Notifications/verifications of new logins (e.g. from new countries), maybe?

### Notes

bootrap inspiration for styling the blog:

* http://blackrockdigital.github.io/startbootstrap-blog-home/
* http://blackrockdigital.github.io/startbootstrap-blog-post/
