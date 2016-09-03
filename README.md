This project is a loose attempt to replace the homepage at https://jabber.at.

It is not yet a finished project or anything.

### Ideas

What we definetly need:

1. blog posts
2. static pages
3. site-like framework (so we can show a different hostname depending on the URL)
4. i18n support (also for articles and pages)

More advanced features

1. accounts.jabber.at integration
2. test.jabber.at integration
3. comments on blog posts

Just a brain storming

1. some account settings integration (e.g. ability to configure MAM settings)
2. security stuff (e.g. from where you logged in recently, ...)
3. notifications/verifications of new logins (e.g. from new countries), maybe?
4. finally a webclient (shouldn't be to hard, there are js libs for it)
5. better social media integration (twitter cards, facebook opengraph tags)
6. calendar export of scheduled downtimes

### TODOs

There are obviously still plenty of todos before the page can go live, without order:

2. Tags for blog posts
3. Importer for data from account.jabber.at
4. Internationalized URLs for URL paths (`/contact/` vs. `/kontakt/`)
5. Provide a webchat
6. Minimized JavaScript/CSS
7. Import Tags from Drupal
8. Automatically convert at least some links from imported Drupal data
9. Add the ability to edit your email address
10. RSS feed
11. Search functionality
12. Comments?

### Notes

bootrap inspiration for styling the blog:

* http://blackrockdigital.github.io/startbootstrap-blog-home/
* http://blackrockdigital.github.io/startbootstrap-blog-post/

### Deployment

In your local git checkout (see Development), create a fabric configuration file:

```
(hp)user@host ~/git/hp $ cat fab.conf 
[jabber.at]
# The domain to deploy to
hostname = jabber.at
# You should be able to ssh into the target server with this command.
host = user@example.com
```

Install the projects dependencies. On Debian/Ubuntu, do (on the target server):

````
apt-get install virtualenv libgpgme11-dev  libmysqlclient-dev
```

Next you can locally execute:

```
fab setup:section=jabber.at
```

To perform the pasic setup steps. You will still write a localsettings.py file and
do the Django setup.


### Development

Clone the project, install dependencies and locally initialize the virtualenv.

```
git clone https://github.com/jabber-at/hp
cd hp
virtualenv -p /usr/bin/python3 .
pip install -U pip setuptools
pip install -r requirements.txt -r reqirements-dev.txt
cd hp
python manage.py migrate
```
