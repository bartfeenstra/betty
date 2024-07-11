"""
Provide the OpenAPI specification.
"""

from betty import about, model
from betty.locale import DEFAULT_LOCALIZER
from betty.model import UserFacingEntity
from betty.project import Project
from betty.serde.dump import DictDump, Dump
from betty.string import kebab_case_to_lower_camel_case


class Specification:
    """
    Build OpenAPI specifications.
    """

    def __init__(self, project: Project):
        self._project = project

    async def build(self) -> DictDump[Dump]:
        """
        Build the OpenAPI specification.
        """
        specification: DictDump[Dump] = {
            "openapi": "3.1.0",
            "servers": [
                {
                    "url": self._project.static_url_generator.generate(
                        "/", absolute=True
                    ),
                }
            ],
            "info": {
                "title": "Betty",
                "version": await about.version_label(),
            },
            "paths": {},
            "components": {
                "responses": {
                    "401": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/betty/response/error",
                                },
                            },
                        },
                    },
                    "403": {
                        "description": "Forbidden",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/betty/response/error",
                                },
                            },
                        },
                    },
                    "404": {
                        "description": "Not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/betty/response/error",
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
                        "$ref": self._project.static_url_generator.generate(
                            "/schema.json#/definitions"
                        ),
                    },
                },
            },
        }

        # Add entity operations.
        for entity_type in await model.ENTITY_TYPE_REPOSITORY.select(UserFacingEntity):
            if self._project.configuration.clean_urls:
                collection_path = f"/{entity_type.plugin_id()}/"
                single_path = f"/{entity_type.plugin_id()}/{{id}}/"
            else:
                collection_path = f"/{entity_type.plugin_id()}/index.json"
                single_path = f"/{entity_type.plugin_id()}/{{id}}/index.json"
            entity_type_label = entity_type.plugin_label().localize(DEFAULT_LOCALIZER)
            specification["paths"].update(  # type: ignore[union-attr]
                {
                    collection_path: {
                        "get": {
                            "summary": f"Retrieve the collection of {entity_type_label} entities.",
                            "responses": {
                                "200": {
                                    "description": f"The collection of {entity_type_label} entities.",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": f"#/components/schemas/betty/response/{kebab_case_to_lower_camel_case(entity_type.plugin_id())}Collection",
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    single_path: {
                        "get": {
                            "summary": f"Retrieve a single {entity_type_label} entity.",
                            "responses": {
                                "200": {
                                    "description": f"The {entity_type_label} entity.",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "$ref": f"#/components/schemas/betty/entity/{kebab_case_to_lower_camel_case(entity_type.plugin_id())}",
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            )

        # Add default behavior to all requests.
        for path in specification["paths"]:  # type: ignore[union-attr]
            specification["paths"][path]["get"]["responses"].update(  # type: ignore[call-overload, index, union-attr]
                {
                    "401": {
                        "$ref": "#/components/responses/401",
                    },
                    "403": {
                        "$ref": "#/components/responses/403",
                    },
                    "404": {
                        "$ref": "#/components/responses/404",
                    },
                }
            )

        return specification
