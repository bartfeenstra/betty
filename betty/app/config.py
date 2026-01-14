"""
Provide application configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import OptionalField, assert_locale, assert_record
from betty.config import Configuration, Sample
from betty.dirs import APP_CONFIG_DIRECTORY_PATH
from betty.locale import DEFAULT_LOCALE, to_language_tag

if TYPE_CHECKING:
    from collections.abc import Iterable

    from babel import Locale

    from betty.serde import SerializedData, SerializedMapping

CONFIGURATION_FILE_PATH = APP_CONFIG_DIRECTORY_PATH / "app.json"


@final
class AppConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.app.App`.

    .. configuration:: betty.app.config:AppConfiguration
    """

    def __init__(
        self,
        *,
        locale: Locale | None = None,
    ):
        super().__init__()
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

    @override
    @classmethod
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(
            **assert_record(OptionalField("locale", assert_locale()))(serialized)
        )

    @override
    def dump(self) -> SerializedMapping[SerializedData]:
        if self.locale is None:
            return {}
        return {"locale": to_language_tag(self.locale)}

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.locale == other.locale

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(cls(locale=DEFAULT_LOCALE), label="Full", full=True)
