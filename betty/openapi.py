"""
Provide the OpenAPI specification.
"""

from json import loads
from pathlib import Path
from typing import Self, final

import aiofiles

from betty import about, model
from betty.json.schema import Schema
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project, ProjectSchema
from betty.serde.dump import Dump, DumpMapping
from betty.string import kebab_case_to_lower_camel_case
from betty.user import UserFacing


class Specification:
    """
    Build OpenAPI specifications.
    """

    def __init__(self, project: Project):
        self._project = project

    async def build(self) -> DumpMapping[Dump]:
        """
        Build the OpenAPI specification.
        """
        url_generator = await self._project.url_generator
        specification: DumpMapping[Dump] = {
            "openapi": "3.1.0",
            "servers": [
                {
                    "url": url_generator.generate("betty-static:///", absolute=True),
                }
            ],
            "info": {
                "title": "Betty",
                "version": about.version_label(),
            },
            "paths": {},
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
        for entity_type in await model.ENTITY_TYPE_REPOSITORY.select(UserFacing):
            await entity_type.linked_data_schema(self._project)
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
                                                "$ref": await ProjectSchema.def_url(
                                                    self._project,
                                                    f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}EntityCollectionResponse",
                                                ),
                                            },
                                        },
                                    },
                                },
                            },
                            "tags": [entity_type_label],
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
                                                "$ref": await ProjectSchema.def_url(
                                                    self._project,
                                                    f"{kebab_case_to_lower_camel_case(entity_type.plugin_id())}Entity",
                                                ),
                                            },
                                        },
                                    },
                                },
                            },
                            "tags": [entity_type_label],
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


@final
class SpecificationSchema(Schema):
    """
    The OpenAPI Specification schema.
    """

    _instance: Self | None = None

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        if cls._instance is None:
            async with aiofiles.open(
                Path(__file__).parent
                / "json"
                / "schemas"
                / "openapi-specification.json"
            ) as f:
                raw_schema = await f.read()
            cls._instance = cls(def_name="openApiSpecification")
            cls._instance._schema = loads(raw_schema)  # type: ignore[assignment]
        return cls._instance
