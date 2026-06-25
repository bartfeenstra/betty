"""
Locale data.
"""

from __future__ import annotations

from typing import final

from babel import Locale

from betty.assertions.locale import assert_locale
from betty.data import DataDefinition
from betty.locale import to_language_tag
from betty.localizables.gettext import _
from betty.porters.callback import CallbackPorter


@final
class LocaleDefinition(DataDefinition[Locale]):
    """
    Define a locale (identifier).
    """

    def __init__(self):
        super().__init__(
            cls=Locale,
            label=_("Locale"),
            description=_('An IETF BCP 47 language tag, such as "nl-NL".'),
            porter=CallbackPorter[Locale](assert_locale(), to_language_tag),
        )
