from gettext import NullTranslations
from os import listdir
from pathlib import Path

from betty.locale import open_translations
from betty.tests import TestCase


class TranslationsTest(TestCase):
    def test(self) -> None:
        assets_directory_path = Path(__file__).parents[3] / 'assets'
        for locale_path_name in listdir(assets_directory_path / 'locale'):
            locale = locale_path_name.replace('_', '-')
            self.assertIsInstance(open_translations(locale, assets_directory_path), NullTranslations)
