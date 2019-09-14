import datetime
import gettext
import os
from typing import Optional

from babel import dates

from betty.ancestry import Date
from betty.config import Locale


def open_translations(locale: Locale, directory_path: str) -> Optional[gettext.GNUTranslations]:
    try:
        with open(os.path.join(directory_path, 'locale', str(locale), 'LC_MESSAGES', 'betty.mo'), 'rb') as f:
            return gettext.GNUTranslations(f)
    except FileNotFoundError:
        return None


def format_date(date: Date, locale: Locale) -> str:
    DATE_FORMATS = {
        (True, True, True): _('MMMM d, y'),
        (True, True, False): _('MMMM, y'),
        (True, False, False): _('y'),
        (False, True, True): _('MMMM d'),
        (False, True, False): _('MMMM'),
    }
    try:
        format = DATE_FORMATS[tuple(map(lambda x: x is not None, date.parts))]
    except KeyError:
        return _('unknown date')
    parts = map(lambda x: 1 if x is None else x, date.parts)
    return dates.format_date(datetime.date(*parts), format, locale)
