"""
The JSON serializer.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final, override

from betty.localizables.gettext import _
from betty.media_types.json import JSON
from betty.portable import PortableData
from betty.serialize import InvalidSerializedData, Serializer, SerializerDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


@final
class InvalidJson(InvalidSerializedData):
    """
    Raised when something is not valid JSON.
    """

    _message = _("Invalid JSON")


@final
@SerializerDefinition("json", label="JSON")
class Json(Serializer):
    """
    .. plugin:: serializer:json.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return JSON.media_type

    @override
    def load(self, serialized: str, /) -> PortableData:
        try:
            return cast(PortableData, json.loads(serialized))
        except json.JSONDecodeError as error:
            raise InvalidJson(serialized) from error

    @override
    def dump(self, portable: PortableData, /) -> str:
        return json.dumps(portable, indent=2, sort_keys=True)
