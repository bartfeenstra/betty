"""
The JSON serializer.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final, override

from betty.json import DumpableJsonData, LoadableJsonData
from betty.localizables.gettext import _
from betty.media_types.json import JSON
from betty.serialize import SerializationError, Serializer, SerializerDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


@final
@SerializerDefinition("json", label="JSON")
class Json(Serializer[LoadableJsonData, DumpableJsonData]):
    """
    .. plugin:: serializer:json.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return JSON.media_type

    @override
    def load(self, serialized: str, /) -> LoadableJsonData:
        try:
            return cast(LoadableJsonData, json.loads(serialized))
        except json.JSONDecodeError as e:
            raise SerializationError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, portable: DumpableJsonData, /) -> str:
        return json.dumps(portable, indent=2, sort_keys=True)
