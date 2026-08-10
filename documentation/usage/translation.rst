Translations
============

Betty is fully multilingual (internationalized), and can be localized to different
`locales <https://en.wikipedia.org/wiki/Locale_(computer_software)>`_, which includes
translations of the built-in US English messages to any language of your choice.

.. seealso::

   View the available translations on `Weblate <https://hosted.weblate.org/projects/betty/>`_.

Each time a message is translated, Betty finds the translation as follows:

#. If the project has a translation in its asset directory, use it
#. If an asset directory plugin has a translation, use it
#. If a built-in translation exists, use it
#. If no translation exists, use the original US English message

Read more about :doc:`asset directories </usage/assets>`.

Project translations
--------------------

Adding a new translation
^^^^^^^^^^^^^^^^^^^^^^^^

Run ``betty new-translation $locale`` where ``$locale`` is an
`IETF BCP 47 language tag <https://tools.ietf.org/html/bcp47>`_.

This will create ``./locale/$locale/betty.po``, which you can then edit yourself.

Updating existing translations after changing translatable messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you've made changes to the translatable messages in your project, run
``betty update-translations`` to update ``betty.pot`` and any ``betty.po``
files for existing translations. You can then edit the updated ``betty.po``
files yourself.

Read more about how to :doc:`contribute to Betty's built-in translations </development>`.
