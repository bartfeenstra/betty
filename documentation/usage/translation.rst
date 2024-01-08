Translations
============

Betty ships with the following translations:

* US English (``en-US``)
* Dutch (``nl-NL``)
* French (``fr-FR``)
* Ukrainian (``uk``)

Extensions and projects can override these translations, or provide translations for additional locales. All locale
information is stored in ``./locale/$locale`` within the assets directories, where ``$locale`` is an
`IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.

Betty uses `gettext <https://www.gnu.org/software/gettext/>`_ to manage its translations. For each language, there must
be a ``./locale/$locale/LC_MESSAGES/betty.po`` file that contains the translations for that language. These translations
are compiled lazily whenever Betty needs them,, so you won't have to go through the trouble of creating ``*.mo`` files
yourself.

Translations are loaded in the following order, where translations loaded later will override earlier translations:

#. Betty's built-in translations
#. Translations provided by extensions in the order of their dependency tree
#. Project-specific translations found in your project's assets directory

Read more about how to :doc:`contribute to Betty's built-in translations </development>`.
