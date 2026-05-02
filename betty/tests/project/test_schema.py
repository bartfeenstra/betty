from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.json_schema import JSON_SCHEMA
from betty.json_schema.validate import validate
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.project.schema import ProjectSchema

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.project import Project
    from betty.test_utils.conftest import IsolatedProjectFactory


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
        self,
        isolated_project_factory: IsolatedProjectFactory,
        request: pytest.FixtureRequest,
    ) -> SchemaTestBaseSut:
        url, clean_urls = request.param
        async with isolated_project_factory(clean_urls=clean_urls, url=url) as project:
            return (
                await ProjectSchema.new(project),
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
    async def test_new(self, clean_urls: bool, isolated_project: Project) -> None:
        sut = await ProjectSchema.new(isolated_project)
        validate(JSON_SCHEMA, sut.schema)

    async def test_def_url(self, isolated_project: Project) -> None:
        def_name = "myFirstDefinition"
        assert def_name in await ProjectSchema.def_url(isolated_project, def_name)

    async def test_url(self, isolated_project: Project) -> None:
        assert "http" in await ProjectSchema.url(isolated_project)

    async def test_www_path(self, isolated_project: Project) -> None:
        assert str(ProjectSchema.www_path(isolated_project))
