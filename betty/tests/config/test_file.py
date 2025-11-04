from json import dumps, loads
from pathlib import Path

import aiofiles
import pytest
from typing_extensions import override

from betty.config.file import assert_configuration_file, write_configuration_file
from betty.error import FileNotFound
from betty.exception import HumanFacingException
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration


class _LoadingDummyConfiguration(DummyConfiguration):
    loaded_dump: Dump

    @override
    def load(self, dump: Dump) -> None:
        self.loaded_dump = dump


async def test_assert_configuration_file__with_file_not_found(tmp_path: Path) -> None:
    configuration = _LoadingDummyConfiguration()
    configuration_file_path = tmp_path / "config.json"
    assertion = await assert_configuration_file(configuration)
    with pytest.raises(FileNotFound):
        assertion(configuration_file_path)


async def test_assert_configuration_file__with_invalid_configuration(
    tmp_path: Path,
) -> None:
    configuration = _LoadingDummyConfiguration()
    configuration_file_path = tmp_path / "config.json"
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write("this is not valid JSON")
    assertion = await assert_configuration_file(configuration)
    with pytest.raises(HumanFacingException):
        assertion(configuration_file_path)


async def test_assert_configuration_file__with_valid_configuration(
    tmp_path: Path,
) -> None:
    configuration = _LoadingDummyConfiguration()
    configuration_file_path = tmp_path / "config.json"
    dump = {"hello": "world!"}
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write(dumps(dump))
    assertion = await assert_configuration_file(configuration)
    assertion(configuration_file_path)
    assert configuration.loaded_dump == dump


class _DumpingDummyConfiguration(DummyConfiguration):
    @override
    def dump(self) -> Dump:
        return {
            "Hello": "world!",
        }


async def test_write_configuration_file(tmp_path: Path) -> None:
    configuration = _DumpingDummyConfiguration()
    configuration_file_path = tmp_path / "config.json"
    await write_configuration_file(configuration, configuration_file_path)
    async with aiofiles.open(configuration_file_path) as f:
        file_contents = await f.read()
    expected = {
        "Hello": "world!",
    }
    assert loads(file_contents) == expected
