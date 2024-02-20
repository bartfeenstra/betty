Translations
============

Betty ships with the following translations:

Dutch (``nl-NL``)
    Translations are {{{ translation-coverage-nl-NL }}}% complete.
English (``en-US``)
    Translations are 100% complete.
French (``fr-FR``)
    Translations are {{{ translation-coverage-fr-FR }}}% complete.
German (``de-DE``)
    Translations are {{{ translation-coverage-de-DE }}}% complete.
Ukrainian (``uk``)
    Translations are {{{ translation-coverage-uk }}}% complete.

Extensions and projects can override these translations through `asset management <assets>`_.

Betty uses `gettext <https://www.gnu.org/software/gettext/>`_ to manage its translations. For each language, there must
be a ``./locale/$locale/LC_MESSAGES/betty.po`` file that contains the translations for that language. These translations
are compiled lazily whenever Betty needs them, so you won't have to go through the trouble of creating ``*.mo`` files
yourself.

Translations are loaded in the following order, where translations loaded later will override earlier translations:

#. Betty's built-in translations
#. Translations provided by extensions in the order of their dependency tree
#. Project-specific translations found in your project's assets directory

Read more about how to :doc:`contribute to Betty's built-in translations </development>`.
