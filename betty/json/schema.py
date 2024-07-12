"""
Provide JSON utilities.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, cast

from jsonschema.validators import Draft202012Validator
from referencing import Resource, Registry

from betty.serde.dump import DumpMapping, Dump, dump_default
from betty.string import upper_camel_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.project import Project

    pass


class Schema:
    """
    Build JSON Schemas for a Betty application.
    """

    def __init__(self, project: Project):
        self._project = project

    async def build(self) -> DumpMapping[Dump]:
        """
        Build the JSON Schema.
        """
        from betty import model

        schema: DumpMapping[Dump] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": self._project.static_url_generator.generate(
                "schema.json", absolute=True
            ),
        }

        definitions = dump_default(schema, "definitions", dict)
        entity_definitions = dump_default(definitions, "entity", dict)
        response_definitions = dump_default(definitions, "response", dict)

        # Add entity schemas.
        async for entity_type in model.ENTITY_TYPE_REPOSITORY:
            entity_type_schema_name = upper_camel_case_to_lower_camel_case(
                entity_type.plugin_id()
            )
            entity_type_schema = await entity_type.linked_data_schema(self._project)
            entity_type_schema_definitions = cast(
                DumpMapping[Dump], entity_type_schema.pop("definitions", {})
            )
            for (
                definition_name,
                definition_schema,
            ) in entity_type_schema_definitions.items():
                if definition_name not in definitions:
                    definitions[definition_name] = definition_schema
            entity_definitions[entity_type_schema_name] = entity_type_schema
            entity_definitions[f"{entity_type_schema_name}Collection"] = {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uri",
                },
            }
            response_definitions[f"{entity_type_schema_name}Collection"] = {
                "type": "object",
                "properties": {
                    "collection": {
                        "$ref": f"#/definitions/entity/{entity_type_schema_name}Collection",
                    },
                },
            }

        # Add the HTTP error response.
        response_definitions["error"] = {
            "type": "object",
            "properties": {
                "$schema": ref_json_schema(schema),
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

    async def validate(self, data: Any) -> None:
        """
        Validate JSON against the Betty JSON schema.
        """
        schema = Resource.from_contents(await self.build())
        schema_registry = schema @ Registry()  # type: ignore[operator, var-annotated]
        validator = Draft202012Validator(
            {
                "$ref": data["$schema"],
            },
            registry=schema_registry,
        )
        validator.validate(data)


def add_property(
    schema: DumpMapping[Dump],
    property_name: str,
    property_schema: DumpMapping[Dump],
    property_required: bool = True,
) -> None:
    """
    Add a property to an object schema.
    """
    schema_properties = dump_default(schema, "properties", dict)
    schema_properties[property_name] = property_schema
    if property_required:
        schema_required = dump_default(schema, "required", list)
        schema_required.append(property_name)


def ref_locale(root_schema: DumpMapping[Dump]) -> DumpMapping[Dump]:
    """
    Reference the locale schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "locale" not in definitions:
        definitions["locale"] = {
            "type": "string",
            "description": "A BCP 47 locale identifier (https://www.ietf.org/rfc/bcp/bcp47.txt).",
        }
    return {
        "$ref": "#/definitions/locale",
    }


def ref_json_schema(root_schema: DumpMapping[Dump]) -> DumpMapping[Dump]:
    """
    Reference the JSON Schema schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "schema" not in definitions:
        definitions["schema"] = {
            "type": "string",
            "format": "uri",
            "description": "A JSON Schema URI.",
        }
    return {
        "$ref": "#/definitions/schema",
    }
