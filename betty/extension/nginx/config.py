"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from typing import Self

from betty.config import Configuration
from betty.serde.dump import Dump, VoidableDump, minimize, Void, VoidableDictDump
from betty.serde.load import Asserter, Fields, OptionalField, Assertions


class NginxConfiguration(Configuration):
    def __init__(
        self,
        *,
        www_directory_path: str | None = None,
        https: bool | None = None,
    ):
        super().__init__()
        self._https = https
        self.www_directory_path = www_directory_path

    @property
    def https(self) -> bool | None:
        return self._https

    @https.setter
    def https(self, https: bool | None) -> None:
        self._https = https
        self._dispatch_change()

    @property
    def www_directory_path(self) -> str | None:
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: str | None) -> None:
        self._www_directory_path = www_directory_path
        self._dispatch_change()

    def update(self, other: Self) -> None:
        self._https = other._https
        self._www_directory_path = other._www_directory_path
        self._dispatch_change()

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(
            Fields(
                OptionalField(
                    "https",
                    Assertions(
                        asserter.assert_or(
                            asserter.assert_bool(), asserter.assert_none()
                        )
                    )
                    | asserter.assert_setattr(configuration, "https"),
                ),
                OptionalField(
                    "www_directory_path",
                    Assertions(asserter.assert_str())
                    | asserter.assert_setattr(configuration, "www_directory_path"),
                ),
            )
        )(dump)
        return configuration

    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            "https": self.https,
            "www_directory_path": (
                Void
                if self.www_directory_path is None
                else str(self.www_directory_path)
            ),
        }
        return minimize(dump, True)
