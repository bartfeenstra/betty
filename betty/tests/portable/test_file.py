from json import dumps, loads
from pathlib import Path

import aiofiles
import pytest

from betty.error import FileNotFound
from betty.exception import HumanFacingException
from betty.portable.file import assert_load_file, dump_file
from betty.test_utils.data import DummyData


async def test_assert_load_file__with_file_not_found(tmp_path: Path) -> None:
    configuration_file_path = tmp_path / "config.json"
    assertion = await assert_load_file()
    with pytest.raises(FileNotFound):
        assertion(configuration_file_path)


async def test_assert_load_file__with_invalid_configuration(
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "config.json"
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write("this is not valid JSON")
    assertion = await assert_load_file()
    with pytest.raises(HumanFacingException):
        assertion(configuration_file_path)


async def test_assert_load_file__with_valid_configuration(
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "config.json"
    value = "world!"
    portable = {"hello": value}
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write(dumps(portable))
    assertion = await assert_load_file()
    assert assertion(configuration_file_path) == portable


async def test_dump_file(tmp_path: Path) -> None:
    value = "Hello, world!"
    configuration = DummyData(value)
    configuration_file_path = tmp_path / "config.json"
    await dump_file(
        configuration.data().porter.dump(configuration), configuration_file_path
    )
    async with aiofiles.open(configuration_file_path) as f:
        file_contents = await f.read()
    expected = {
        "value": value,
    }
    assert loads(file_contents) == expected
