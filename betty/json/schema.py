"""
Provide JSON utilities.
"""

from __future__ import annotations

from collections.abc import MutableSequence
from json import loads
from pathlib import Path
from typing import Any, TYPE_CHECKING, final, Self, cast

import aiofiles
from jsonschema.validators import Draft202012Validator
from referencing import Resource, Registry

from betty.serde.dump import DumpMapping, Dump
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.project import Project


class Schema:
    """
    A JSON Schema.
    """

    def __init__(
        self, *, name: str | None = None, schema: DumpMapping[Dump] | None = None
    ):
        self._name = name
        self.__schema = schema or {}
        self.__schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"

    @property
    def schema(self) -> DumpMapping[Dump]:
        """
        The raw JSON Schema.
        """
        return self.__schema

    @property
    def definitions(self) -> DumpMapping[Dump]:
        """
        The JSON Schema's definitions, kept separately, so they can be merged when this schema is embedded.

        Only top-level definitions are supported. You **MUST NOT** nest definitions. Instead, prefix or suffix
        their names.
        """
        return cast(DumpMapping[Dump], self.schema.setdefault("definitions", {}))

    def embed(self, into: Schema) -> Dump:
        """
        Embed this schema.
        """
        for name, schema in self.definitions.items():
            into.definitions[name] = schema
        schema = {
            child_name: child_schema
            for child_name, child_schema in self.schema.items()
            if child_name != "definitions"
        }
        if self._name is None:
            return schema
        into.definitions[self._name] = schema
        return Ref(self._name).embed(into)

    def validate(self, data: Any) -> None:
        """
        Validate data against this schema.
        """
        schema = Resource.from_contents(self.schema)
        schema_registry = schema @ Registry()  # type: ignore[operator, var-annotated]
        validator = Draft202012Validator(
            self.schema,
            registry=schema_registry,
        )
        validator.validate(data)


class ArraySchema(Schema):
    """
    A JSON Schema array.
    """

    def __init__(self, items_schema: Schema, *, name: str | None = None):
        super().__init__(name=name)
        self.schema["type"] = "array"
        self.schema["items"] = items_schema.embed(self)


class Ref(Schema):
    """
    A JSON Schema that references a definition.
    """

    def __init__(self, definition_name: str):
        super().__init__(schema={"$ref": f"#/definitions/{definition_name}"})


@final
class ProjectSchema(Schema):
    """
    A JSON Schema for a project.
    """

    @classmethod
    async def new(cls, project: Project) -> Self:
        """
        Create a new schema for the given project.
        """
        from betty import model

        schema = cls()
        schema.schema["$id"] = project.static_url_generator.generate(
            "schema.json", absolute=True
        )

        # Add entity schemas.
        async for entity_type in model.ENTITY_TYPE_REPOSITORY:
            entity_type_schema = await entity_type.linked_data_schema(project)
            entity_type_schema.embed(schema)
            schema.definitions[
                f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}Collection"
            ] = {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uri",
                },
            }
            schema.definitions[
                f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}CollectionResponse"
            ] = {
                "type": "object",
                "properties": {
                    "collection": {
                        "$ref": f"#/definitions/{kebab_case_to_lower_camel_case(entity_type.plugin_id())}Collection",
                    },
                },
            }

        # Add the HTTP error response.
        schema.definitions["errorResponse"] = {
            "type": "object",
            "properties": {
                "$schema": JsonSchemaReference().embed(schema),
                "message": {
                    "type": "string",
                },
            },
            "required": [
                "$schema",
                "message",
            ],
            "additionalProperties": False,
        }

        return schema


def add_property(
    into: Schema,
    property_name: str,
    property_schema: Schema,
    property_required: bool = True,
) -> None:
    """
    Add a property to an object schema.
    """
    schema_properties = cast(
        DumpMapping[Dump], into.schema.setdefault("properties", {})
    )
    schema_properties[property_name] = property_schema.embed(into)
    if property_required:
        schema_required = cast(
            MutableSequence[str], into.schema.setdefault("required", [])
        )
        schema_required.append(property_name)


class LocaleSchema(Schema):
    """
    The JSON Schema for locales.
    """

    def __init__(self):
        super().__init__(
            name="locale",
            schema={
                "type": "string",
                "description": "A BCP 47 locale identifier (https://www.ietf.org/rfc/bcp/bcp47.txt).",
            },
        )


class JsonSchemaReference(Schema):
    """
    The JSON Schema schema.
    """

    def __init__(self):
        super().__init__(
            name="jsonSchemaReference",
            schema={
                "type": "string",
                "format": "uri",
                "description": "A JSON Schema URI.",
            },
        )


class JsonSchemaSchema(Schema):
    """
    The JSON Schema schema.
    """

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        async with aiofiles.open(
            Path(__file__).parent.parent
            / "test_utils"
            / "json"
            / "json-schema-schema.json"
        ) as f:
            raw_schema = await f.read()
        return cls(name="jsonSchema", schema=loads(raw_schema))
