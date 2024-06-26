from pathlib import Path
from typing import Any, TYPE_CHECKING

import pytest

from betty.extension.nginx.config import NginxConfiguration
from betty.serde.load import AssertionFailed
from betty.tests.serde import raises_error

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestNginxConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: dict[str, Any] = {}
        NginxConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            NginxConfiguration().load(dump)

    @pytest.mark.parametrize(
        "https",
        [
            None,
            True,
            False,
        ],
    )
    async def test_load_with_https(self, https: bool | None) -> None:
        dump: Dump = {
            "https": https,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.https == https

    async def test_load_with_www_directory_path(self, tmp_path: Path) -> None:
        www_directory_path = str(tmp_path)
        dump: Dump = {
            "www_directory_path": www_directory_path,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.www_directory_path == www_directory_path

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = NginxConfiguration()
        expected = {
            "https": None,
        }
        assert expected == sut.dump()

    async def test_dump_with_www_directory_path(self, tmp_path: Path) -> None:
        www_directory_path = str(tmp_path)
        sut = NginxConfiguration()
        sut.www_directory_path = www_directory_path
        expected = {
            "https": None,
            "www_directory_path": www_directory_path,
        }
        assert expected == sut.dump()

    async def test_update(self, tmp_path: Path) -> None:
        www_directory_path = str(tmp_path)
        sut = NginxConfiguration()
        other = NginxConfiguration()
        other.https = True
        other.www_directory_path = www_directory_path
        sut.update(other)
        assert sut.https is True
        assert sut.www_directory_path == www_directory_path
