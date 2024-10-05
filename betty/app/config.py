"""
Provide application configuration.
"""

from __future__ import annotations

from typing import final, Self

from typing_extensions import override

from betty import fs
from betty.assertion import assert_record, OptionalField, assert_str, assert_locale
from betty.config import Configuration
from betty.serde.dump import Dump, minimize, DumpMapping
from betty.typing import void_none

CONFIGURATION_FILE_PATH = fs.HOME_DIRECTORY_PATH / "app.json"


@final
class AppConfiguration(Configuration):
    """
    Provide configuration for :py:class:`betty.app.App`.
    """

    def __init__(
        self,
        *,
        locale: str | None = None,
    ):
        super().__init__()
        self._locale: str | None = locale

    @property
    def locale(self) -> str | None:
        """
        The application locale.
        """
        return self._locale

    async def set_locale(self, locale: str) -> str | None:
        """
        Set :py:attr:`betty.app.config.AppConfiguration.locale`.
        """
        self._locale = await assert_locale()(locale)
        return self.locale

    @override
    def update(self, other: Self) -> None:
        self._locale = other._locale

    @override
    async def load(self, dump: Dump) -> None:
        await assert_record(OptionalField("locale", assert_str() | self.set_locale))(
            dump
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        return minimize({"locale": void_none(self.locale)})
