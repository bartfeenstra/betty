"""
The YAML serializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

import yaml

from betty import media_types
from betty.localizables.gettext import _
from betty.serialize import InvalidSerializedData, Serializer, SerializerDefinition
from betty.typing import is_runtime_checkable_mapping, is_runtime_checkable_sequence
from betty.validators.portable import is_portable_data

if TYPE_CHECKING:
    from betty.media_type import MediaType
    from betty.portable import PortableData


@final
class InvalidYaml(InvalidSerializedData):
    """
    Raised when something is not valid YAML.
    """

    _message = _("Invalid YAML")


@final
@SerializerDefinition("yaml", label="YAML")
class Yaml(Serializer):
    """
    .. plugin:: serializer:yaml.
    """

    @override
    @classmethod
    def media_type(cls) -> MediaType:
        return media_types.yaml.media_type

    @override
    def load(self, serialized: str, /) -> PortableData:
        try:
            return is_portable_data(yaml.safe_load(serialized))
        except yaml.YAMLError as error:
            raise InvalidYaml(serialized) from error

    @override
    def dump(self, portable: PortableData, /) -> str:
        return yaml.safe_dump(_make_dumpable(portable), default_flow_style=False)


def _make_dumpable(value: PortableData) -> PortableData:
    # Work around a bug where ``str`` subclasses cannot be serialized to YAML.
    if isinstance(value, str):
        return str(value)
    if is_runtime_checkable_sequence(value):
        return tuple(map(_make_dumpable, value))
    if is_runtime_checkable_mapping(value):
        # Convert unsupported portable mappings to :py:class:`dict`.
        return {str(key): _make_dumpable(value) for key, value in value.items()}
    return value
