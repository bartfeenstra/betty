from typing import override

import pytest

from betty.media_type import MediaTypeDefinition
from betty.portable import PortableData
from betty.serialize import (
    SerializationError,
    Serializer,
    SerializerDefinition,
    serializer_for,
)


class _Serializer(Serializer):
    @override
    def load(self, serialized: str, /) -> PortableData:
        return None  # pragma: nocover

    @override
    def dump(self, portable: PortableData, /) -> str:
        return ""  # pragma: nocover


@SerializerDefinition(
    "one", MediaTypeDefinition("test-one", label="-", extension=".one"), label="One"
)
class SerializerOne(_Serializer):
    pass


def test_serializer_for__with_supported_type() -> None:
    serializer = SerializerOne()
    assert serializer_for([serializer], ".one") is serializer


def test_serializer_for_with_unsupported_type() -> None:
    with pytest.raises(SerializationError):
        serializer_for([], ".unknown")
