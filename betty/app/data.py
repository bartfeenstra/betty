"""
Data for applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional
from betty.dirs import APP_CONFIG_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE, ResolvableLocale, resolve_locale
from betty.locale.data import LocaleProperty
from betty.locale.localizable.gettext import _
from betty.sample import Size

if TYPE_CHECKING:
    from pathlib import Path


@final
@ObjectDefinition(
    label=_("Application configuration"),
    samples=[
        lambda: Sample(AppConfiguration(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            AppConfiguration(locale=DEFAULT_LOCALE), label="Full", size=Size.FULL
        ),
    ],
)
class AppConfiguration(Data):
    """
    Configuration for :py:class:`betty.app.App`.

    .. data:: betty.app.data:AppConfiguration
    """

    FILE: Final[Path] = APP_CONFIG_DIRECTORY_PATH / "app.json"

    locale = Optional(LocaleProperty())
    """
    The application locale.
    """

    def __init__(self, *, locale: ResolvableLocale | None = None):
        self.locale = None if locale is None else resolve_locale(locale)
