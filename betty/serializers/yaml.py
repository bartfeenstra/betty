"""
The YAML serializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, final, override

import yaml

from betty.localizables.gettext import _
from betty.media_types.yaml import YAML
from betty.serialize import SerializationError, Serializer, SerializerDefinition
from betty.yaml import (
    DumpableYamlData,
    LoadableYamlData,
    YamlData,
    yaml_mapping_types,
    yaml_sequence_types,
)

if TYPE_CHECKING:
    from betty.media_type import MediaType


@final
@SerializerDefinition("yaml", label="YAML")
class Yaml(Serializer[LoadableYamlData, DumpableYamlData]):
    """
    .. plugin:: serializer:yaml.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return YAML.media_type

    @override
    def load(self, serialized: str, /) -> LoadableYamlData:
        try:
            return cast(LoadableYamlData, yaml.safe_load(serialized))
        except yaml.YAMLError as e:
            raise SerializationError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, portable: DumpableYamlData, /) -> str:
        return yaml.safe_dump(_safe_str(portable), default_flow_style=False)


def _safe_str(value: YamlData) -> YamlData:
    # Work around a bug where ``str`` subclasses cannot be serialized to YAML.
    if isinstance(value, str):
        if type(value) is str:
            return value
        return str(value)
    if isinstance(value, yaml_mapping_types):
        return dict(
            zip(
                map(_safe_str, value.keys()),
                map(_safe_str, value.values()),
                strict=False,
            )
        )
    if isinstance(value, yaml_sequence_types):
        return tuple(map(_safe_str, value))
    return value
