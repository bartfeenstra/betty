"""
Provide serialization formats.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final

import yaml
from typing_extensions import override

from betty.locale.localizable.gettext import _
from betty.media_type.media_types import JSON, YAML
from betty.serde import SerializedData
from betty.serde.format import Format, FormatDefinition, FormatError

if TYPE_CHECKING:
    from betty.media_type import MediaType
    from betty.typing import Void


@final
@FormatDefinition("json", label="JSON")
class Json(Format):
    """
    .. plugin:: format:json.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return JSON

    @override
    def load(self, serialized: str, /) -> SerializedData:
        try:
            return cast(SerializedData, json.loads(serialized))
        except json.JSONDecodeError as e:
            raise FormatError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, serialized: SerializedData | Void, /) -> str:
        return json.dumps(serialized, indent=2, sort_keys=True)


@final
@FormatDefinition("yaml", label="YAML")
class Yaml(Format):
    """
    .. plugin:: format:yaml.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return YAML

    @override
    def load(self, serialized: str, /) -> SerializedData:
        try:
            return cast(SerializedData, yaml.safe_load(serialized))
        except yaml.YAMLError as e:
            raise FormatError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, serialized: SerializedData | Void, /) -> str:
        return yaml.safe_dump(serialized)
