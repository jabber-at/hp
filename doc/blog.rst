####
blog
####

***************************************
Sharing, syndication and search engines
***************************************

General resources:

* `Google on meta descriptions <https://support.google.com/webmasters/answer/35624?hl=en>`_
* `Twitter cards <https://dev.twitter.com/cards/types/summary>`_,
  `reference <https://dev.twitter.com/cards/markup>`_
* `Facebook OpenGraph reference <https://developers.facebook.com/docs/sharing/webmasters>`_
* `RSS specification <http://www.rssboard.org/rss-specification>`_
* `Atom specification <https://validator.w3.org/feed/docs/rfc4287.html>`_

Title
=====

======== ==========================================================================================
What
======== ==========================================================================================
Facebook "A clear title without branding or mentioning the domain itself."
Twitter  Max. 70 characters
======== ==========================================================================================

Descriptions
============

Various description formats that we should support:

========= ====== ====== ==========================================================================
What      Format Length Description
========= ====== ====== ==========================================================================
preview   html   any    What we display as preview on the blog front page.
meta      plain  160    What search engines displays as article description.

                        ``<meta name='Description" content="....">``
RSS2      either any    The RSS2 ``description`` tag.
Atom      either any    The Atom ``summary`` tag.
Twitter   plain  200    The ``twitter:description`` card tag.
OpenGraph plain  ?      Docs say "between 2 and 4 sentences", but examples only have one sentence.
========= ====== ====== ==========================================================================

Images
======

======== =========================================================================================
What     Description
======== =========================================================================================
Google
Atom     For feeds as a whole: ``icon`` should be quare, ``logo`` is "larger", aspect ratio 2:1.
         I couldn't find any spec stating any recommended/min/max sizes.
RSS2     For feeds as a whole: Maximum is 144x400px, default is 88x31px.
Twitter  Minimum 120x120px, must be less then 1MB, cropped to a square.
Facebook Minimum 200x200px (but < 600x315 for "small images"), aspect ratio 1.91:1.

         See also:
         `Best practices <https://developers.facebook.com/docs/sharing/best-practices#images>`_
======== =========================================================================================
