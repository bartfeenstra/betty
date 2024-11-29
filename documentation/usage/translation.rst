Translations
============

Betty is fully multilingual (internationalized), and can be localized to different
`locales <https://en.wikipedia.org/wiki/Locale_(computer_software)>`_, which includes
translations of the built-in US English messages to any language of your choice.

Each time a message is translated, Betty finds the translation as follows:

#. If the project has a translation in its assets directory, use it
#. If an extension has a translation in its assets directory, use it
#. If a built-in translation exists, use it
#. If no translation exists, use the original US English message

Read more about :doc:`asset directories </usage/assets>`.

gettext
-------

Betty uses `gettext <https://www.gnu.org/software/gettext/>`_ to manage its translations:

- Betty will compile ``*.mo`` files internally. You will never have to do this manually
- Betty will manage ``*.pot`` and ``*.po`` files automatically if you use the ``*-translations`` commands
- You will have to add translations to ``*.po`` files yourself

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

Built-in translations
---------------------

Betty ships with the following translations:

Arabic (``ar``)
    Translations are {{{ translation-coverage-ar }}}% complete.
Dutch (``nl-NL``)
    Translations are {{{ translation-coverage-nl-NL }}}% complete.
English (``en-US``)
    Translations are 100% complete.
French (``fr-FR``)
    Translations are {{{ translation-coverage-fr-FR }}}% complete.
German (``de-DE``)
    Translations are {{{ translation-coverage-de-DE }}}% complete.
Hebrew (``he``)
    Translations are {{{ translation-coverage-he }}}% complete.
Ukrainian (``uk``)
    Translations are {{{ translation-coverage-uk }}}% complete.

Read more about how to :doc:`contribute to Betty's built-in translations </development>`.
