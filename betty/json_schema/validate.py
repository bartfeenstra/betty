from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from betty.json_schema import Schema

if TYPE_CHECKING:
    from betty.portable import PortableMapping


def validate(schema: Schema | PortableMapping | bool, data: Any, /) -> None:
    """
    Validate data against a schema.

    :raise jsonschema.exceptions.ValidationError:
    """
    schema_registry = Resource.from_contents(schema) @ Registry()
    validator = Draft202012Validator(
        schema.schema if isinstance(schema, Schema) else schema,
        registry=schema_registry,
    )
    validator.validate(data)
