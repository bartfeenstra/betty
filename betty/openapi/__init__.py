"""
Provide the OpenAPI specification.
"""

from betty import about
from betty.entity import EntityDefinition as EntityDefinition
from betty.locale.localize import default_localizer
from betty.portable import PortableMapping
from betty.project import Project
from betty.project.schema import ProjectSchema
from betty.string import kebab_case_to_lower_camel_case


class Specification:
    """
    Build OpenAPI specifications.
    """

    def __init__(self, project: Project, /):
        self._project = project

    async def build(self) -> PortableMapping:
        """
        Build the OpenAPI specification.
        """
        url_generator = await self._project.url_generator
        specification_paths: PortableMapping[PortableMapping] = {}
        specification: PortableMapping = {
            "openapi": "3.1.0",
            "servers": [
                {
                    "url": url_generator.generate("betty-static:///", absolute=True),
                }
            ],
            "info": {
                "title": "Betty",
                "version": about.version_label,
            },
            "paths": specification_paths,
            "components": {
                "responses": {
                    "401": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": await ProjectSchema.def_url(
                                        self._project, "errorResponse"
                                    ),
                                },
                            },
                        },
                    },
                    "403": {
                        "description": "Forbidden",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": await ProjectSchema.def_url(
                                        self._project, "errorResponse"
                                    ),
                                },
                            },
                        },
                    },
                    "404": {
                        "description": "Not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": await ProjectSchema.def_url(
                                        self._project, "errorResponse"
                                    ),
                                },
                            },
                        },
                    },
                },
                "parameters": {
                    "id": {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "description": "The ID for the resource to retrieve.",
                        "schema": {
                            "type": "string",
                        },
                    },
                },
                "schemas": {
                    "betty": {
                        "$ref": await ProjectSchema.url(self._project),
                    },
                },
            },
        }

        # Add entity operations.
        async for entity_type in self._project.plugins[EntityDefinition]:
            if not entity_type.public_facing:
                continue
            await entity_type.cls.linked_data_schema(self._project)
            if self._project.clean_urls:
                collection_path = f"/{entity_type.id}/"
                single_path = f"/{entity_type.id}/{{id}}/"
            else:
                collection_path = f"/{entity_type.id}/index.json"
                single_path = f"/{entity_type.id}/{{id}}/index.json"
            entity_type_label = entity_type.label.localize(default_localizer)
            specification_paths[collection_path] = {
                "get": {
                    "summary": f"Retrieve the collection of {entity_type_label} entities.",
                    "responses": {
                        "200": {
                            "description": f"The collection of {entity_type_label} entities.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": await ProjectSchema.def_url(
                                            self._project,
                                            f"{kebab_case_to_lower_camel_case(entity_type.id)}EntityCollectionResponse",
                                        ),
                                    },
                                },
                            },
                        },
                    },
                    "tags": [entity_type_label],
                },
            }
            specification_paths[single_path] = {
                "get": {
                    "summary": f"Retrieve a single {entity_type_label} entity.",
                    "responses": {
                        "200": {
                            "description": f"The {entity_type_label} entity.",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": await ProjectSchema.def_url(
                                            self._project,
                                            f"{kebab_case_to_lower_camel_case(entity_type.id)}Entity",
                                        ),
                                    },
                                },
                            },
                        },
                    },
                    "tags": [entity_type_label],
                },
            }

        # Add default behavior to all requests.
        for path_specification in specification_paths.values():
            path_specification["get"]["responses"].update({
                "401": {
                    "$ref": "#/components/responses/401",
                },
                "403": {
                    "$ref": "#/components/responses/403",
                },
                "404": {
                    "$ref": "#/components/responses/404",
                },
            })

        return specification
