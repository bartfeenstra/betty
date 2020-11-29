import gettext
from os import path, listdir

from betty.locale import open_translations
from betty.tests import TestCase

_ASSETS_DIRECTORY_PATH = path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), 'assets')


class TranslationsTest(TestCase):
    def test(self) -> None:
        for locale_path_name in listdir(path.join(_ASSETS_DIRECTORY_PATH, 'locale')):
            locale = locale_path_name.replace('_', '-')
            self.assertIsInstance(open_translations(locale, _ASSETS_DIRECTORY_PATH), gettext.NullTranslations)
