import pytest
from typing_extensions import override

from betty.media_type import MediaType
from betty.portable import PortableData
from betty.serde import (
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


@SerializerDefinition("one", label="One")
class SerializerOne(_Serializer):
    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return MediaType("text/x.betty.test.one", extensions=[".one"])


@SerializerDefinition("two", label="Two")
class SerializerTwo(_Serializer):
    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return MediaType("text/x.betty.test.two", extensions=[".two"])


def test_serializer_for__with_supported_type() -> None:
    assert serializer_for([SerializerOne.plugin()], ".one") is SerializerOne.plugin()


def test_serializer_for_with_unsupported_type() -> None:
    with pytest.raises(SerializationError):
        serializer_for([], ".unknown")
