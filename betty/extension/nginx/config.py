"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from typing import Self

from typing_extensions import override

from betty.config import Configuration
from betty.serde.dump import Dump, VoidableDump, minimize, VoidableDictDump
from betty.typing import Void
from betty.assertion import (
    OptionalField,
    assert_record,
    assert_or,
    assert_bool,
    assert_none,
    assert_setattr,
    assert_str,
)


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

    @property
    def www_directory_path(self) -> str | None:
        """
        The nginx server's public web root directory path.
        """
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: str | None) -> None:
        self._www_directory_path = www_directory_path

    @override
    def update(self, other: Self) -> None:
        self._https = other._https
        self._www_directory_path = other._www_directory_path

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField(
                "https",
                assert_or(assert_bool(), assert_none()) | assert_setattr(self, "https"),
            ),
            OptionalField(
                "www_directory_path",
                assert_str() | assert_setattr(self, "www_directory_path"),
            ),
        )(dump)

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
