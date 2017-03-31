################
Creating content
################

The ``blog`` app contains three different models to create content:

* A **Page** is intended as a static page.
* A **Blog post** is a page for the front page blog. It's like a page, but with just a few extra properties.
* An **Image** allows a content creator to upload images. Images don't show up anywhere by default, but can be
  included in pages or blog posts.

All content can be created in the Admin interface at ``/admin/``.

*******
TinyMCE
*******

`TinyMCE <https://www.tinymce.com/>`_ is used for all HTML-formatted text. It is somewhat tuned to integrate
with Bootstrap:

* Tables are created with the ``table`` class Bootstrap uses for styling tables.

  * Extra buttons in the "Table" menu are provided to make tables striped, bordered or condensed or make rows
    hover. The "Responsive" button wraps the table in a div to make the table responsive on small devices.
  * Row- and Cell-Properties can be set for contextual background.

* Use the "Formats" menu to create alerts and contextual text classes.
* The main menu also includes submenus for Bootstrap labels and Glyphicons.

**********
Templating
**********

Pages and Blog posts are rendered as templates, which means you can use any standard Django templating
constructs in them, e.g.::

   {% page_url "clients" as clients_url %}

   {% if clients_url %}
      This is only visible if you have a page with the slug "clients".
   {% endif %}

Some extra context variables are also available:

============== ================================================================================
Variable       Description
============== ================================================================================
FACEBOOK_PAGE  The ``FACEBOOK_PAGE`` setting.
TWITTER_HANDLE The ``TWITTER_HANDLE`` setting.
default_site   The default site from the ``DEFAULT_XMPP_HOST`` setting.
object         The current page or blog post (use e.g. ``{{ object.title.current }}``).
other_langs    All languages *except* the current one.
site           The currently used site from the ``XMPP_HOSTS`` setting.
============== ================================================================================

So for example you could write::

   Welcome to {{ site.BRAND }}. Our Twitter username is {{ TWITTER_HANDLE }}.

Template tags
=============

The custom templatetags described here are available in all blog posts and pages. You don't have to use the
``{% use %}`` template tag to load them, just do, for example::

   Please see {% page 23 title="this page" %}

Core
====

.. automodule:: core.templatetags.core
   :members:
   :exclude-members: os_selector

Blogs/Pages
===========

.. automodule:: blog.templatetags.blog
   :members:

Bootstrap
=========

.. automodule:: bootstrap.templatetags.bootstrap
   :members:

****************
CSS conveniences
****************

* Add the ``colored-glyphicon`` class to any element to consistently color some of the contained Glypicons:

  * "Question Sign" will be grey.
  * "OK" will be green.
  * "Remove" will be red.

*********
Footnotes
*********

Use the **Insert/edit footnote** button in TinyMCE to insert a footnote. Footnotes are automatically numbered,
hovering over them will display a tooltip text. They are implemented purely in CSS, with no Javascript or
server-side code required. Note that "footnote" is somewhat a misnomer, in that the text is never displayed
at the bottom of the page.

The tooltip can contain raw HTML, e.g. ``See <a href="...">here</a>.``. The footnote text is optional, in case
you do not want to display any text. This is useful for example if you want to add a footnote next to a link,
but with no extra text.

Footnotes are a simple ``<span>`` element and will merge with any style in similar context (e.g. with a
Glyphicon)

To remove a footnote, simply edit the footnote again and don't set any tooltip text.

TinyMCE is not very easy to extend in that even basic functionality requires a lot of Javascript code. As
such, the buttons behaviour is far from perfect:

* Footnotes don't handle very well if used without any text. The cursor is never in the context of the
  footnote, it thus can't easily be altered or removed.
* Because the footnote style merges with Glypicons, removing a footnote on a Glyphicon also removes it.

*******************
OS-specific content
*******************

The ``os-*`` CSS classes can be used to display content only for specific operating systems. Content using the
classes will be hidden unless the user appears to be using the specific platform. We use this functionality
for our `clients page <https://jabber.at/p/clients/>`_.

The following operating system classes are available:

========== ================================
CSS class  Description
========== ================================
os-osx     MacOS X (apple Desktop machines)
os-linux   Linux or any Unix derivate
os-ios     Apple iOS (iPhone, iPad, ...)
os-android Google Android
os-win     Microsoft Windows
========== ================================

You can use multiple classes as well, e.g. ``<span class="os-linux os-win">Only Linux and Windows</a>``.

You can always force a particular platform by appending the URL with the ``os`` query parameter. For example,
https://jabber.at/p/clients/?os=android will always display android related content.

You can also add a select box to allow the user to choose his operating system and display content
appropriately using the :py:func:`core.templatetags.core.os_selector` tag::

   {% os_selector %}

.. autofunction:: core.templatetags.core.os_selector

There are a few meta-classes available:

=========== ============================================================
CSS class   Description
=========== ============================================================
os-mobile   Displays on both iOS and Android
os-console  Displays if the user selects "Linux (console)" and on Linux.
os-browser  Displays if the user selects "Browser"
=========== ============================================================
