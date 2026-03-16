from typing import TYPE_CHECKING, override

import pytest

from betty.plugins.serializer.json import Json
from betty.serde import SerializationError, Serializer
from betty.test_utils.serde import SerializerTestBase

if TYPE_CHECKING:
    from betty.portable import PortableData


class TestJson(SerializerTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Serializer:
        return Json()

    def test_load__with_invalid_dump(self) -> None:
        with pytest.raises(SerializationError):
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
