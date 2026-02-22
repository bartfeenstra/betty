"""
Locale data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from babel import Locale

from betty.assertion import assert_locale
from betty.data import DataDefinition
from betty.locale import resolve_locale, to_language_tag
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter
from betty.property import Property

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


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


@final
class LocaleProperty(Property):
    """
    A property containing a locale.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocaleDefinition(),
            label=label,
            description=description,
            resolver=resolve_locale,
        )
