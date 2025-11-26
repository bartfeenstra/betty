"""
Provide application configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.assertion import OptionalField, assert_locale, assert_record, assert_setattr
from betty.config import Configuration
from betty.dirs import APP_CONFIG_DIRECTORY_PATH
from betty.locale import to_language_tag

if TYPE_CHECKING:
    from babel import Locale

    from betty.serde.dump import Dump, DumpMapping

CONFIGURATION_FILE_PATH = APP_CONFIG_DIRECTORY_PATH / "app.json"


@final
class AppConfiguration(Configuration):
    """
    Provide configuration for :py:class:`betty.app.App`.
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
        self.assert_mutable()
        self._locale = locale

    @override
    def load(self, dump: Dump, /) -> None:
        self.assert_mutable()
        assert_record(
            OptionalField("locale", assert_locale() | assert_setattr(self, "locale"))
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        if self.locale is None:
            return {}
        return {"locale": to_language_tag(self.locale)}
