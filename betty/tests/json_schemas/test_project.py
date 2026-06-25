from __future__ import annotations

from typing import TYPE_CHECKING

from betty.json_schema import validate
from betty.json_schemas.json_schema import json_schema_schema
from betty.json_schemas.project import (
    new_project_schema,
    project_schema_def_url,
    project_schema_url,
    project_schema_www_path,
)

if TYPE_CHECKING:
    from betty.project import Project


async def test_new_project_schema(isolated_project: Project) -> None:
    sut = await new_project_schema(isolated_project)
    validate(json_schema_schema, sut)


async def test_project_schema_def_url(isolated_project: Project) -> None:
    def_name = "myFirstDefinition"
    assert def_name in await project_schema_def_url(isolated_project, def_name)


async def test_project_schema_url(isolated_project: Project) -> None:
    assert "http" in await project_schema_url(isolated_project)


async def test_project_schema_www_path(isolated_project: Project) -> None:
    assert str(project_schema_www_path(isolated_project))
