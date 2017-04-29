################
Customize JS/CSS
################


**********************
Build custom libraries
**********************

We use `fabric-webbuilders <https://github.com/mathiasertl/fabric-webbuilders>`_
to build customized versions of jQuery and Bootstrap.

jQuery
======

Build a custom version of jQuery (latest 2.x version)::

   fab build_jquery

or e.g a different version with different modules (see `Modules
<https://github.com/jquery/jquery#modules>`_, we assume that you *know* what you are doing here)::

   fab build_jquery:version=2.1.3,excludes=-effects

Bootstrap
=========

Build a custom version of Bootstrap (latest 3.x version)::

   fab build_bootstrap

Bootstrap has no built-in support for building a customized version locally. ``fabric-webbuilders`` has
somewhat shakey support for passing a ``config.json`` file as generated at `Customize and download
<http://getbootstrap.com/customize/>`_. By default, ``fab build_bootstrap`` already passes a file to minimize
JS/CSS size, but you can pass a different config as well::

   fab build_bootstrap:config=/path/to/config.json

If you run into problems with this, you are advised to use the custom builder on their homepage instead.

Prism
=====

We use `Prism <http://prismjs.com/>`_ for syntax highlighting.

.. TODO:: Add ability to build custom version
