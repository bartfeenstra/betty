Static translations
===================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.locale.localizable.config.StaticTranslationsLocalizableConfiguration`

All configuration options
-------------------------

This configuration is either a single translation as a string,
or multiple translations as a key-value mapping.

A single translation
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  string

A single translation can be set that is to be used for all languages.

Example configuration:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          "I am a single translation, used for all languages"

   .. tab-item:: JSON

      .. code-block:: json

          "I am a single translation, used for all languages"

Multiple translations
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  mapping
            Keys (string) are `IETF BCP 47 language tags <https://en.wikipedia.org/wiki/IETF_language_tag>`_,
            and values (string) are human-readable translations.

Example configuration:

.. tab-set::

   .. tab-item:: YAML

      .. code-block:: yaml

          en-US: "I'm the English translation"
          nl-NL: "Ik ben de Nederlandse vertaling"

   .. tab-item:: JSON

      .. code-block:: json

          {
            "en-US": "I'm the English translation",
            "nl-NL": "Ik ben de Nederlandse vertaling",
          }