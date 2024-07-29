Templating
==========

.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1
   :titlesonly:

   templating/*

Templating is the task of building HTML pages by taking an HTML **template** and to fill it with information unique a page.

Betty uses `Jinja2 <https://jinja.palletsprojects.com>`_ to parse ``*.j2`` templates. This allows your HTML or other code to
receive data from your ancestry, read configuration, any much more.

Adding or overriding templates
------------------------------
Any template file can be overridden by adding a file with the same name to the same subdirectory within your extension
or project's :ref:`assets directory <The assets directory>`.

In this section
---------------
- :doc:`/usage/templating/globals`
- :doc:`/usage/templating/filters`
- :doc:`/usage/templating/tests`
