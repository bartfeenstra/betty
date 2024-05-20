"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from typing import Self

from typing_extensions import override

from betty.config import Configuration
from betty.serde.dump import Dump, VoidableDump, minimize, Void, VoidableDictDump
from betty.serde.load import Asserter, Fields, OptionalField, Assertions


class NginxConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.extension.nginx.Nginx` extension.
    """

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
        """
        Whether the nginx server should use HTTPS.

        :return: ``True`` to use HTTPS (and HTTP/2), ``False`` to use HTTP (and HTTP 1), ``None``
            to let this behavior depend on whether the project's base URL uses HTTPS or not.
        """
        return self._https

    @https.setter
    def https(self, https: bool | None) -> None:
        self._https = https
        self._dispatch_change()

    @property
    def www_directory_path(self) -> str | None:
        """
        The nginx server's public web root directory path.
        """
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: str | None) -> None:
        self._www_directory_path = www_directory_path
        self._dispatch_change()

    @override
    def update(self, other: Self) -> None:
        self._https = other._https
        self._www_directory_path = other._www_directory_path
        self._dispatch_change()

    @override
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

    @override
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
