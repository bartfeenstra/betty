"""
The YAML serializer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

import yaml

from betty import content_types
from betty.assertions.portable import assert_portable_data
from betty.localizables.gettext import _
from betty.serialize import SerializationError, Serializer, SerializerDefinition
from betty.typing import is_runtime_checkable_mapping, is_runtime_checkable_sequence

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
@SerializerDefinition("yaml", content_types.yaml, label="YAML")
class Yaml(Serializer):
    """
    .. plugin:: serializer:yaml.
    """

    @override
    def load(self, serialized: str, /) -> PortableData:
        try:
            return assert_portable_data(yaml.safe_load(serialized))
        except yaml.YAMLError as e:
            raise SerializationError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

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
