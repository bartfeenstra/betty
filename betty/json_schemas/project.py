"""
JSON schemas for projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.entity import EntityDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from pathlib import Path

    from betty.portable import PortableMapping
    from betty.project import Project


async def project_schema_def_url(project: Project, def_name: str) -> str:
    """
    Get the URL to a project's JSON Schema definition.
    """
    return f"{await project_schema_url(project)}#/$defs/{def_name}"


async def project_schema_url(project: Project) -> str:
    """
    Get the URL to a project's JSON Schema.
    """
    url_generator = await project.url_generator
    return url_generator.generate("betty-static:///schema.json", absolute=True)


def project_schema_www_path(project: Project) -> Path:
    """
    Get the path to the schema file in a site's public WWW directory.
    """
    return project.www_directory / "schema.json"


async def new_project_schema(project: Project) -> PortableMapping:
    """
    Create a JSON Schema for a project.
    """
    defs = {}
    entity_type_schemas = []
    async for entity_type in project.plugins[EntityDefinition]:
        entity_type_schema = await entity_type.cls.linked_data_schema(project)
        entity_type_schemas.append((entity_type, entity_type_schema))
        defs.update(entity_type_schema.defs)
    return {
        "$id": await project_schema_url(project),
        "anyOf": [{"$ref": f"#/$defs/{def_name}"} for def_name in defs],
        **{
            f"{kebab_case_to_lower_camel_case(entity_type.id)}EntityCollectionResponse": {
                "type": "object",
                "properties": {
                    "collection": {
                        "items": {
                            "description": "A reference to an entity's JSON resource",
                            "format": "uri",
                            "title": "Entity",
                            "type": "string",
                        },
                        "title": "Entities",
                        "description": "References to entities' JSON resources",
                        "type": "array",
                    },
                },
            }
            for entity_type, entity_type_schema in entity_type_schemas
        },
        "errorResponse": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                },
            },
            "required": [
                "message",
            ],
            "additionalProperties": False,
        },
        "$defs": defs,
    }
