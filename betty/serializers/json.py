"""
The JSON serializer.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final, override

from betty.json import JsonData
from betty.localizables.gettext import _
from betty.media_types.json import JSON
from betty.serialize import SerializationError, Serializer, SerializerDefinition
from betty.typing import is_runtime_checkable_mapping, is_runtime_checkable_sequence

if TYPE_CHECKING:
    from betty.media_type import MediaType
    from betty.portable import PortableData


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
            return cast(JsonData, json.loads(serialized))
        except json.JSONDecodeError as e:
            raise SerializationError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, portable: PortableData, /) -> str:
        return json.dumps(_make_dumpable(portable), indent=2, sort_keys=True)


def _make_dumpable(value: PortableData) -> JsonData:
    if is_runtime_checkable_sequence(value):
        return tuple(map(_make_dumpable, value))
    if is_runtime_checkable_mapping(value):
        # Convert unsupported portable mappings to :py:class:`dict`.
        return {str(key): _make_dumpable(value) for key, value in value.items()}
    return value
