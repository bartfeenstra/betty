"""
Data for applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from betty.data import Data, OptionalDefinition, Sample
from betty.data.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.dirs import APP_CONFIG_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE
from betty.locale.data import LocaleDefinition
from betty.locale.localizable.gettext import _
from betty.sample import Size

if TYPE_CHECKING:
    from pathlib import Path

    from babel import Locale


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

    def __init__(
        self,
        *,
        locale: Locale | None = None,
    ):
        self._locale: Locale | None = locale

    @property
    @AttrDefinition(OptionalDefinition(LocaleDefinition()))
    def locale(self) -> Locale | None:
        """
        The application locale.
        """
        return self._locale

    @locale.setter
    def locale(self, locale: Locale | None) -> None:
        self._locale = locale
