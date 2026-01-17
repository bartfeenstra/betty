from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.plugin import PluginDefinition
from betty.serde import Format, FormatError
from betty.serde.formats import Json, Yaml
from betty.test_utils.serde.format import FormatDefinitionTestBase, FormatTestBase

if TYPE_CHECKING:
    from betty.portable import PortableData


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
        portable = sut.load('{"hello": [123, "World!"]}')
        expected = {"hello": [123, "World!"]}
        assert portable == expected

    def test_dump(self) -> None:
        portable: PortableData = {"hello": [123, "World!"]}
        sut = Json()
        serialized = sut.dump(portable)
        assert (
            serialized
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
        serialized = "hello:\n- 123\n- World!\n"
        portable = sut.load(serialized)
        expected = {"hello": [123, "World!"]}
        assert expected == portable

    def test_dump(self) -> None:
        portable: PortableData = {"hello": [123, "World!"]}
        sut = Yaml()
        serialized = sut.dump(portable)
        assert serialized == "hello:\n- 123\n- World!\n"
