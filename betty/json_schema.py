"""
The JSON Schema API.

All schemas using this API **MUST** follow JSON Schema Draft 2020-12.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from jsonschema.validators import Draft202012Validator
from referencing import Registry, Resource

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from betty.portable import PortableData, PortableMapping


def embed_json_schema(
    schema: PortableMapping, *, defs: MutableMapping[str, PortableMapping]
) -> PortableMapping:
    """
    Embed a schema into another.
    """
    if isinstance(schema, Mapping) and "$defs" in schema:
        defs.update(schema["$defs"])
        return {key: value for key, value in schema.items() if key != "$defs"}
    return schema


def validate(schema: PortableMapping | bool, data: PortableData, /) -> None:
    """
    Validate data against a schema.

    :raises jsonschema.exceptions.ValidationError:
    """
    schema_registry = Resource.from_contents(schema) @ Registry()
    validator = Draft202012Validator(schema, registry=schema_registry)
    validator.validate(data)
