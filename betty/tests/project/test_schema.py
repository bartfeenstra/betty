from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.json.schema import JsonSchemaSchema
from betty.project import Project
from betty.project.schema import ProjectSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.app import App


class TestProjectSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[tuple[str, bool]]:
        for url in (
            "http://example.com",
            "https://example.com",
            "https://example.com/root-path",
        ):
            for clean_urls in (True, False):
                yield url, clean_urls

    @override
    @pytest.fixture(params=_sut_params())
    async def sut_data(
        self, isolated_app: App, request: pytest.FixtureRequest
    ) -> SchemaTestBaseSut:
        url, clean_urls = request.param
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.url = url
            project.configuration.clean_urls = clean_urls
            async with project:
                return (
                    await ProjectSchema.new(services=project),
                    [
                        await Person().dump_linked_data(project),
                        await Place().dump_linked_data(project),
                        await Event().dump_linked_data(project),
                    ],
                    [],
                )

    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_new(self, clean_urls: bool, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await ProjectSchema.new(services=project)
        JsonSchemaSchema().validate(sut.schema)

    async def test_def_url(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            def_name = "myFirstDefinition"
            assert def_name in await ProjectSchema.def_url(project, def_name)

    async def test_url(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            assert "http" in await ProjectSchema.url(project)

    async def test_www_path(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            assert str(ProjectSchema.www_path(project))
