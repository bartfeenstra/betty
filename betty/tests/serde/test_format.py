import pytest

from betty.serde.dump import Dump
from betty.serde.format import Yaml, Json
from betty.serde.load import FormatError


class TestJson:
    async def test_load_with_invalid_json(self) -> None:
        sut = Json()
        json_dump = "@"
        with pytest.raises(FormatError):
            sut.load(json_dump)

    async def test_load_with_valid_json(self) -> None:
        sut = Json()
        json_dump = '{"hello": [123, "World!"]}'
        dump = sut.load(json_dump)
        expected = {"hello": [123, "World!"]}
        assert expected == dump

    async def test_dump(self) -> None:
        dump: Dump = {"hello": [123, "World!"]}
        sut = Json()
        json_dump = sut.dump(dump)
        assert '{"hello": [123, "World!"]}' == json_dump


class TestYaml:
    async def test_load_with_invalid_yaml(self) -> None:
        sut = Yaml()
        yaml_dump = "@"
        with pytest.raises(FormatError):
            sut.load(yaml_dump)

    async def test_load_with_valid_yaml(self) -> None:
        sut = Yaml()
        yaml_dump = "hello:\n- 123\n- World!\n"
        dump = sut.load(yaml_dump)
        expected = {"hello": [123, "World!"]}
        assert expected == dump

    async def test_dump(self) -> None:
        dump: Dump = {"hello": [123, "World!"]}
        sut = Yaml()
        yaml_dump = sut.dump(dump)
        assert "hello:\n- 123\n- World!\n" == yaml_dump
