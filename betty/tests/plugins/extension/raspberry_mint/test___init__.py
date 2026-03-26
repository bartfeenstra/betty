from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.content import ContentManufacturer
from betty.model import EntityDefinition
from betty.plugins.content.static import Static
from betty.plugins.extension.raspberry_mint import (
    RaspberryMint,
)
from betty.plugins.extension.raspberry_mint.region import Region
from betty.project import Project
from betty.project.data import EntityTypeConfiguration
from betty.project.generate import generate
from betty.test_utils.model import DummyEntityOne
from betty.tests.conftest import check_skip_webpack_entry_point_provider

if TYPE_CHECKING:
    from betty.app import App


class TestRaspberryMint:
    @pytest.mark.parametrize(
        ("expected", "primary_color"),
        [
            (RaspberryMint.DEFAULT_PRIMARY_COLOR, None),
            ("#aabbcc", "#aabbcc"),
        ],
    )
    async def test_primary_color(
        self, expected: str, primary_color: str | None, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(project=project, primary_color=primary_color) as sut,
        ):
            assert sut.primary_color == expected

    @pytest.mark.parametrize(
        ("expected", "secondary_color"),
        [
            (RaspberryMint.DEFAULT_SECONDARY_COLOR, None),
            ("#aabbcc", "#aabbcc"),
        ],
    )
    async def test_secondary_color(
        self, expected: str, secondary_color: str | None, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(project=project, secondary_color=secondary_color) as sut,
        ):
            assert sut.secondary_color == expected

    @pytest.mark.parametrize(
        ("expected", "tertiary_color"),
        [
            (RaspberryMint.DEFAULT_TERTIARY_COLOR, None),
            ("#aabbcc", "#aabbcc"),
        ],
    )
    async def test_tertiary_color(
        self, expected: str, tertiary_color: str | None, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(project=project, tertiary_color=tertiary_color) as sut,
        ):
            assert sut.tertiary_color == expected

    async def test_regional_content__without_regions(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(project=project) as sut,
        ):
            assert await sut.regional_content == {}

    async def test_regional_content__with_region_without_content(
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(
                project=project, regional_content={Region.FRONT_PAGE_CONTENT: []}
            ) as sut,
        ):
            assert await sut.regional_content == {Region.FRONT_PAGE_CONTENT.value: []}

    async def test_regional_content__with_region_with_content(
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            RaspberryMint(
                project=project,
                regional_content={
                    Region.FRONT_PAGE_CONTENT: [ContentManufacturer(Static)]
                },
            ) as sut,
        ):
            assert isinstance(
                (await sut.regional_content)[Region.FRONT_PAGE_CONTENT.value][0], Static
            )

    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate__html_list_for_third_party_entity(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(
            isolated_app,
            plugins={EntityDefinition: [DummyEntityOne]},
            service_plugins=[RaspberryMint],
        ) as project:
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
