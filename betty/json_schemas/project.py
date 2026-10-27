"""
JSON schemas for the project API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.factory import Manufacturable
from betty.json_schema import JsonSchemaReference, Schema
from betty.project import Project

if TYPE_CHECKING:
    from pathlib import Path


@final
class ProjectSchema(Manufacturable, Schema):
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
        return project.www_directory / "schema.json"

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        schema = cls()
        schema.schema["$id"] = await cls.url(project)

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

        schema.schema["anyOf"] = [
            {"$ref": f"#/$defs/{def_name}"} for def_name in schema.defs
        ]

        return schema
