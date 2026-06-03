from typing import override

import pytest

from betty.serialize import SerializationError, Serializer
from betty.serializers.yaml import Yaml
from betty.test_utils.serialize import SerializerTestBase


class TestYaml(SerializerTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Serializer:
        return Yaml()

    def test_load__with_invalid_dump(self) -> None:
        with pytest.raises(SerializationError):
            Yaml().load(": :InvalidYaml: :")

    def test_load__with_valid_dump(self) -> None:
        sut = Yaml()
        serialized = "hello:\n- 123\n- World!\n"
        portable = sut.load(serialized)
        expected = {"hello": [123, "World!"]}
        assert expected == portable

    def test_dump(self) -> None:
        sut = Yaml()
        serialized = sut.dump(
            {"hello": [123, "World!"]},  # ty:ignore[invalid-argument-type]
        )
        assert serialized == "hello:\n- 123\n- World!\n"
