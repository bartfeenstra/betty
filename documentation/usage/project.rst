Projects
========

.. toctree::
   :glob:
   :hidden:
   :maxdepth: 1
   :titlesonly:

   project/*

A project contains all the information necessary to turn a family tree into a site. After installing
Betty once, you can manage multiple projects.

You can create and tailor projects using :doc:`configuration files </usage/project/configuration>`.


.. important::
    Betty will consider the directory your project configuration file is located in to be your project directory,
    and assumes that the directory will not be used for anything else besides your Betty project.


The project directory
--------------------

``assets/``
^^^^^^^^^^^
Your project's :doc:`assets </usage/assets>`, through which you can override translations, HTML templates, and more.

``betty.yaml`` **or** ``betty.yml`` **or** ``betty.json``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Your project's configuration file.

``output/``
^^^^^^^^^^^
This is where Betty puts all the things it generates for you.

``output/www/``
^^^^^^^^^^^^^^^
This is where Betty puts your generated site.

In this section
---------------
- :doc:`/usage/project/configuration`
