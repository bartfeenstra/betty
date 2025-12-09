"""
JSON schemas for the project API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.json.schema import JsonSchemaReference, Schema
from betty.model import EntityDefinition
from betty.model.schema import ToManySchema
from betty.project.factory import ProjectDependentSelfFactory
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from pathlib import Path

    from betty.project import Project


@final
class ProjectSchema(ProjectDependentSelfFactory, Schema):
    """
    A JSON Schema for a project.
    """

    @classmethod
    async def def_url(cls, project: Project, def_name: str) -> str:
        """
        Get the URL to a project's JSON Schema definition.
        """
        return f"{await cls.url(project)}#/$defs/{def_name}"

    @classmethod
    async def url(cls, project: Project) -> str:
        """
        Get the URL to a project's JSON Schema.
        """
        url_generator = await project.url_generator
        return url_generator.generate("betty-static:///schema.json", absolute=True)

    @classmethod
    def www_path(cls, project: Project) -> Path:
        """
        Get the path to the schema file in a site's public WWW directory.
        """
        return project.www_directory_path / "schema.json"

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        schema = cls()
        schema._schema["$id"] = await cls.url(project)

        # Add entity schemas.
        for entity_type in await project.plugins(EntityDefinition):
            entity_type_schema = await entity_type.cls.linked_data_schema(project)
            entity_type_schema.embed(schema)
            def_name = f"{kebab_case_to_lower_camel_case(entity_type.id)}EntityCollectionResponse"
            schema.defs[def_name] = {
                "type": "object",
                "properties": {
                    "collection": ToManySchema().embed(schema),
                },
            }

        # Add the HTTP error response.
        schema.defs["errorResponse"] = {
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

        schema._schema["anyOf"] = [
            {"$ref": f"#/$defs/{def_name}"} for def_name in schema.defs
        ]

        return schema
