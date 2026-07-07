from json import dumps, loads
from pathlib import Path

import pytest

from betty.error import FileNotFound
from betty.exception import HumanFacingException
from betty.portable.file import assert_load_file, dump_file
from betty.serializers.json import Json
from betty.test_utils.data import DummyData


def test_assert_load_file__with_file_not_found(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    assertion = assert_load_file(serializers=[])
    with pytest.raises(FileNotFound):
        assertion(file)


def test_assert_load_file__with_invalid_data(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    with open(file, "w", encoding="utf-8") as f:
        f.write("this is not valid JSON")
    assertion = assert_load_file(serializers=[Json()])
    with pytest.raises(HumanFacingException):
        assertion(file)


def test_assert_load_file__with_valid_data(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    value = "world!"
    portable = {"hello": value}
    with open(file, "w", encoding="utf-8") as f:
        f.write(dumps(portable))
    assertion = assert_load_file(serializers=[Json()])
    assert assertion(file) == portable


async def test_dump_file(tmp_path: Path) -> None:
    value = "Hello, world!"
    configuration = DummyData(value)
    file = tmp_path / "config.json"
    await dump_file(
        DummyData.data().porter.dump(configuration), file, serializers=[Json()]
    )
    with open(file, encoding="utf-8") as f:
        file_contents = f.read()
    expected = {
        "value": value,
    }
    assert loads(file_contents) == expected
