from typing import override

import pytest

from betty.plugins.serializer.json import Json
from betty.serde import SerializationError, Serializer
from betty.test_utils.serde import SerializerTestBase


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
        sut = Json()
        serialized = sut.dump(
            {"hello": [123, "World!"]},  # ty:ignore[invalid-argument-type]
        )
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
