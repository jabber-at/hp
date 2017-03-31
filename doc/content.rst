################
Content overview
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

*************
Template tags
*************

****************
CSS conveniences
****************

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
