from json import dumps, loads
from pathlib import Path

import pytest

from betty.portable.file import dump_file, is_load_file
from betty.serializers.json import Json
from betty.test_utils.data import DummyData
from betty.user.error import UserFacingError
from betty.validators.path import NotFound


def test_is_load_file__with_file_not_found(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    validator = is_load_file(serializers=[])
    with pytest.raises(NotFound):
        validator(file)


def test_is_load_file__with_invalid_data(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    with open(file, "w", encoding="utf-8") as f:
        f.write("this is not valid JSON")
    validator = is_load_file(serializers=[Json()])
    with pytest.raises(UserFacingError):
        validator(file)


def is_load_file__with_valid_data(tmp_path: Path) -> None:
    file = tmp_path / "config.json"
    value = "world!"
    portable = {"hello": value}
    with open(file, "w", encoding="utf-8") as f:
        f.write(dumps(portable))
    validator = is_load_file(serializers=[Json()])
    assert validator(file) == portable


async def test_dump_file(tmp_path: Path) -> None:
    value = "Hello, world!"
    configuration = DummyData(value)
    file = tmp_path / "config.json"
    await dump_file(
        DummyData.definition.porter.dump(configuration), file, serializers=[Json()]
    )
    with open(file, encoding="utf-8") as f:
        file_contents = f.read()
    expected = {
        "value": value,
    }
    assert loads(file_contents) == expected
