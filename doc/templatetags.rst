####################
Custom template tags
####################

The custom templatetags described here are available in all blog posts and
pages. If you want to use them in a template on the filesystem, you must load
the ``use`` templatetag::

   {% use blog %}

   Please see {% page 23 title="this page" %}

******************
Core functionality
******************

.. automodule:: core.templatetags.core
   :members:

.. automodule:: core.templatetags.canonical
   :members:

.. automodule:: core.templatetags.render
   :members:

***********
Blogs/Pages
***********

.. automodule:: blog.templatetags.blog
   :members:

*********
Bootstrap
*********

.. automodule:: bootstrap.templatetags.bootstrap
   :members:
