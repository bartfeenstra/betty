from __future__ import annotations

from typing import TYPE_CHECKING

from betty.extension.raspberry_mint import RaspberryMint, RaspberryMintConfiguration
from betty.model import EntityDefinition
from betty.project import Project
from betty.project.config import EntityTypeConfiguration
from betty.project.generate import generate
from betty.test_utils.model import DummyEntityOne
from betty.tests.conftest import check_skip_webpack_entry_point_provider

if TYPE_CHECKING:
    from betty.app import App


class TestRaspberryMint:
    async def test_configuration(self, isolated_app: App) -> None:
        configuration = RaspberryMintConfiguration()
        async with Project.new_isolated(isolated_app) as project, project:
            sut = RaspberryMint(project=project, configuration=configuration)
            assert sut.configuration is configuration

    async def test_filters(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await RaspberryMint.new(services=project) as sut,
        ):
            assert sut.filters

    @check_skip_webpack_entry_point_provider
    async def test_generate__html_list_for_third_party_entity(
        self, isolated_app: App
    ) -> None:
        with EntityDefinition.type().discoverer.override(DummyEntityOne):
            async with Project.new_isolated(isolated_app) as project:
                project.configuration.extensions.add(RaspberryMint)
                project.configuration.entity_types.add(
                    EntityTypeConfiguration(
                        entity_type=DummyEntityOne, generate_html_list=True
                    )
                )
                async with project:
                    await generate(project)
                assert (
                    project.www_directory / DummyEntityOne.plugin().id / "index.html"
                ).is_file()

    async def test_regions(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await RaspberryMint.new(services=project)
            assert await sut.regions
