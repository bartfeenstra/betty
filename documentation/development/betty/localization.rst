Localization
============

gettext
-------

Betty uses `gettext <https://www.gnu.org/software/gettext/>`_ to manage its translations:

- Betty will compile ``*.mo`` files internally. You will never have to do this manually
- Betty will manage ``*.pot`` and ``*.po`` files automatically if you use the ``*-translations`` commands
- You will have to add translations to ``*.po`` files yourself

Working on translatable strings
-------------------------------

Run ``betty dev-update-translations`` to update the translations files with the changes you made.


Translating Betty
-----------------

The Betty community uses `Weblate <https://hosted.weblate.org/projects/betty/betty/>`_ to coordinate translations
of its built-in translatable strings. To add or improve translations, create a Weblate account, navigate to the
Betty translation you want to contribute to, and start translating.

Changes made in Weblate will be synchronized back to Betty in the form of
`pull requests <https://github.com/bartfeenstra/betty/pulls>`_ once every 24 hours.
