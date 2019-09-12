import gettext
import os
from typing import Optional

from betty.config import Locale


def open_translations(locale: Locale, directory_path: str) -> Optional[gettext.GNUTranslations]:
    try:
        with open(os.path.join(directory_path, 'locale', str(locale), 'LC_MESSAGES', 'betty.mo'), 'rb') as f:
            return gettext.GNUTranslations(f)
    except FileNotFoundError:
        return None
