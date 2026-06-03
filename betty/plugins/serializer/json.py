"""
The JSON serializer.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final, override

from betty.locale.localizable.gettext import _
from betty.media_types.json import JSON
from betty.portable import PortableData
from betty.serde import SerializationError, Serializer, SerializerDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


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
        except json.JSONDecodeError as e:
            raise SerializationError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, portable: PortableData, /) -> str:
        return json.dumps(portable, indent=2, sort_keys=True)
