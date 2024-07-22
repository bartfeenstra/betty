"""
Provide application configuration.
"""

from __future__ import annotations

from typing import final, Self

from betty import fs
from betty.assertion import (
    assert_record,
    OptionalField,
    assert_str,
    assert_setattr,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.locale import get_data, LocaleNotFoundError
from betty.locale.localizable import _
from betty.serde.dump import Dump, VoidableDump, minimize, void_none
from typing_extensions import override

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

    @locale.setter
    def locale(self, locale: str) -> None:
        try:
            get_data(locale)
        except LocaleNotFoundError:
            raise AssertionFailed(
                _('"{locale}" is not a valid IETF BCP 47 language tag.').format(
                    locale=locale
                )
            ) from None
        self._locale = locale

    @override
    def update(self, other: Self) -> None:
        self._locale = other._locale

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("locale", assert_str() | assert_setattr(self, "locale"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize({"locale": void_none(self.locale)}, True)
