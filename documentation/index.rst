Betty Documentation
===================

.. toctree::
   :hidden:
   :includehidden:
   :maxdepth: 1
   :titlesonly:

   installation
   usage
   development
   API Documentation <modindex>
   glossary
   About <about>

Betty visualizes and publishes your family history by building interactive, encyclopedia-like genealogy websites out of your
`Gramps <https://gramps-project.org/>`_ and `GEDCOM <https://en.wikipedia.org/wiki/GEDCOM>`_ family trees.

Features
--------
Betty generates generates a :term:`static site` from your genealogy records. This means that once your site has been
generated, you will not need any special software to publish it. It's **fast and secure**.

* Builds pages for people, places, events, and media
* Renders interactive maps and family trees
* Privacy by default
* Fully multilingual: localize the site to one or more languages of your choice
* `Responsive <https://en.wikipedia.org/wiki/Responsive_web_design>`_, and mobile- and touch-friendly interface


.. grid:: 2
    :gutter: 2 3 4 5

    .. grid-item-card:: Getting started
        :columns: 12 6 6 6

        .. code-block:: python

               pip install betty

        :doc:`More installation options </installation>`

    .. grid-item-card:: See what Betty can do
        :columns: 12 6 6 6
        :text-align: center

        .. button-link:: https://ancestry.bartfeenstra.com
            :color: primary
            :shadow:

            View an example site
