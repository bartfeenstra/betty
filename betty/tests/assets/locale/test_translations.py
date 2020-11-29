import gettext
import glob
from os import path
from unittest import TestCase

_LOCALES_DIRECTORY_PATH = path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), 'assets', 'locale')


class TranslationsTest(TestCase):
    def test(self) -> None:
        locale_paths = glob.glob(path.join(_LOCALES_DIRECTORY_PATH, '**'))
        for locale_path in locale_paths:
            locale_directory_name = path.basename(locale_path)
            with open(path.join(_LOCALES_DIRECTORY_PATH, locale_directory_name, 'LC_MESSAGES', 'betty.mo'), 'rb') as f:
                gettext.GNUTranslations(f)
