"""
The YAML serializer.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast, final, override

import yaml

from betty.locale.localizable.gettext import _
from betty.plugins.media_type.yaml import YAML
from betty.portable import PortableData
from betty.serde import SerializationError, Serializer, SerializerDefinition

if TYPE_CHECKING:
    from betty.media_type import MediaType


@final
@SerializerDefinition("yaml", label="YAML")
class Yaml(Serializer):
    """
    .. plugin:: serializer:yaml.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return YAML.media_type

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
        return yaml.safe_dump(_safe_str(portable))


def _safe_str(value: PortableData) -> PortableData:
    # Work around a bug where ``str`` subclasses cannot be serialized to YAML.
    if isinstance(value, str):
        if type(value) is str:
            return value
        return str(value)
    if isinstance(value, Mapping):
        return dict(
            zip(
                map(
                    _safe_str,  # ty:ignore[invalid-argument-type]
                    value.keys(),
                ),
                map(
                    _safe_str,  # ty:ignore[invalid-argument-type]
                    value.values(),
                ),
                strict=False,
            )
        )  # ty:ignore[invalid-return-type]
    if isinstance(value, Sequence):
        return list(
            map(
                _safe_str,  # ty:ignore[invalid-argument-type]
                value,
            )
        )  # ty:ignore[invalid-return-type]
    return value
