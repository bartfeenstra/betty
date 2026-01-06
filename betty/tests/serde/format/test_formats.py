from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.plugin import PluginDefinition
from betty.serde.format import Format, FormatError
from betty.serde.format.formats import Json, Yaml
from betty.test_utils.serde.format import FormatDefinitionTestBase, FormatTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestJsonDefinition(FormatDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Json.plugin()


class TestJson(FormatTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Format:
        return Json()

    def test_load__with_invalid_dump(self) -> None:
        with pytest.raises(FormatError):
            Json().load("InvalidJson")

    def test_load__with_valid_dump(self) -> None:
        sut = Json()
        actual = sut.load('{"hello": [123, "World!"]}')
        expected = {"hello": [123, "World!"]}
        assert actual == expected

    def test_dump(self) -> None:
        dump: Dump = {"hello": [123, "World!"]}
        sut = Json()
        actual = sut.dump(dump)
        assert (
            actual
            == """
{
  "hello": [
    123,
    "World!"
  ]
}
""".strip()
        )


class TestYamlDefinition(FormatDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Yaml.plugin()


class TestYaml(FormatTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Format:
        return Yaml()

    def test_load__with_invalid_dump(self) -> None:
        with pytest.raises(FormatError):
            Yaml().load(": :InvalidYaml: :")

    def test_load__with_valid_dump(self) -> None:
        sut = Yaml()
        yaml_dump = "hello:\n- 123\n- World!\n"
        dump = sut.load(yaml_dump)
        expected = {"hello": [123, "World!"]}
        assert expected == dump

    def test_dump(self) -> None:
        dump: Dump = {"hello": [123, "World!"]}
        sut = Yaml()
        yaml_dump = sut.dump(dump)
        assert yaml_dump == "hello:\n- 123\n- World!\n"
