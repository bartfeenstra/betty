"""
Common serializers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast, final

import yaml
from typing_extensions import override

from betty.locale.localizable.gettext import _
from betty.media_type.media_types import JSON, YAML
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
        return JSON

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


@final
@SerializerDefinition("yaml", label="YAML")
class Yaml(Serializer):
    """
    .. plugin:: serializer:yaml.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return YAML

    @override
    def load(self, serialized: str, /) -> PortableData:
        try:
            return cast(PortableData, yaml.safe_load(serialized))
        except yaml.YAMLError as e:
            raise SerializationError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, portable: PortableData, /) -> str:
        return yaml.safe_dump(self._safe_str(portable))

    def _safe_str(self, value: PortableData) -> PortableData:
        # Work around a bug where ``str`` subclasses cannot be serialized to YAML.
        if isinstance(value, str):
            return str(value)
        if isinstance(value, Mapping):
            return dict(
                zip(
                    map(self._safe_str, value.keys()),  # ty:ignore[invalid-argument-type]
                    map(self._safe_str, value.values()),  # ty:ignore[invalid-argument-type]
                    strict=False,
                )
            )
        if isinstance(value, Sequence):
            return list(map(self._safe_str, value))  # ty:ignore[invalid-argument-type]
        return value
