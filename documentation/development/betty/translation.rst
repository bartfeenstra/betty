Working on Betty's translations
===============================

Making changes to the translatable strings in the source code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``betty dev-update-translations`` to update the translations files with the changes you made.

Adding translations for a language for which no translations exist yet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``betty dev-new-translation $locale`` where ``$locale`` is an
`IETF BCP 47 language tag <https://tools.ietf.org/html/bcp47>`_.
