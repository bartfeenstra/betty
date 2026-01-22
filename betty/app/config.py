"""
Provide application configuration.
"""

from __future__ import annotations

from typing import final

from babel import Locale

from betty.assertion import assert_locale
from betty.data import Data, DataDefinition, Sample
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.dirs import APP_CONFIG_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE, to_language_tag
from betty.locale.localizable.gettext import _
from betty.portable import CallbackPorter

CONFIGURATION_FILE_PATH = APP_CONFIG_DIRECTORY_PATH / "app.json"


@final
@ObjectDefinition(
    label=_("Application configuration"),
    fields=[
        FieldDefinition(
            Attr("locale"),
            DataDefinition(
                cls=Locale,
                label=_("Locale"),
                porter=CallbackPorter(assert_locale(), to_language_tag),
                empty=lambda data: data is None,
            ),
            required=False,
        ),
    ],
    samples=[
        lambda: Sample(AppConfiguration(), label="Minimal", minimal=True),
        lambda: Sample(
            AppConfiguration(locale=DEFAULT_LOCALE), label="Full", full=True
        ),
    ],
)
class AppConfiguration(Data):
    """
    Configuration for :py:class:`betty.app.App`.

    .. data:: betty.app.config:AppConfiguration
    """

    def __init__(
        self,
        *,
        locale: Locale | None = None,
    ):
        self._locale: Locale | None = locale

    @property
    def locale(self) -> Locale | None:
        """
        The application locale.
        """
        return self._locale

    @locale.setter
    def locale(self, locale: Locale | None) -> None:
        self._locale = locale
