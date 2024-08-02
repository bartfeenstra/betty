Static translations
===================

Static translations  in the data model are stored :py:class:`betty.locale.localizable.StaticTranslationsLocalizable`.

Attribute values
----------------
Attributes of this type will always return a mapping where keys are `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_
language tags and values are human-readable translation strings for the key's locale. Example:


.. code-block:: python

    {
      "en-US": "I'm the English translation",
      "nl-NL": "Ik ben de Nederlandse vertaling",
    }

Setting translations
--------------------
The following examples are for an object ``owner`` on which a static translations attribute names
``translations`` exists.

A single translation
^^^^^^^^^^^^^^^^^^^^
You can assign a single translation as a string. This will internally be stored for the
**undetermined** locale (``und``), and used to localize he attribute to any locale.

.. code-block:: python

    owner.translations = "I'm the English translation"


Multiple translations
^^^^^^^^^^^^^^^^^^^^^

To assign more than one translation, or a single translation for a specific locale, use
the same mapping format as returned by the attribute:

.. code-block:: python

    owner.translations = {
      "en-US": "I'm the English translation",
      "nl-NL": "Ik ben de Nederlandse vertaling",
    }
