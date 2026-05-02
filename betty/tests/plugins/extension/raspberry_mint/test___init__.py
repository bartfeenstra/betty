from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.content import ContentManufacturer
from betty.plugins.content.static import Static
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.raspberry_mint.region import Region
from betty.project.generate import generate
from betty.tests.conftest import check_skip_webpack_entry_point_provider

if TYPE_CHECKING:
    from betty.app import App
    from betty.project import Project
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestRaspberryMint:
    @pytest.mark.parametrize(
        ("expected", "primary_color"),
        [
            (RaspberryMint.DEFAULT_PRIMARY_COLOR, None),
            ("#aabbcc", "#aabbcc"),
        ],
    )
    async def test_primary_color(
        self, expected: str, primary_color: str | None, isolated_project: Project
    ) -> None:
        async with (
            RaspberryMint(project=isolated_project, primary_color=primary_color) as sut,
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
        self, expected: str, secondary_color: str | None, isolated_project: Project
    ) -> None:
        async with (
            RaspberryMint(
                project=isolated_project, secondary_color=secondary_color
            ) as sut,
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
        self, expected: str, tertiary_color: str | None, isolated_project: Project
    ) -> None:
        async with (
            RaspberryMint(
                project=isolated_project, tertiary_color=tertiary_color
            ) as sut,
        ):
            assert sut.tertiary_color == expected

    async def test_regional_content__with_defaults(
        self, isolated_project: Project
    ) -> None:
        async with RaspberryMint(project=isolated_project) as sut:
            assert (await sut.regional_content)[Region.ENTITY_PAGE_CONTENT]

    async def test_regional_content__with_region_without_content(
        self, isolated_project: Project
    ) -> None:
        async with RaspberryMint(
            project=isolated_project, regional_content={Region.FRONT_PAGE_CONTENT: []}
        ) as sut:
            assert (await sut.regional_content)[Region.FRONT_PAGE_CONTENT] == []

    async def test_regional_content__with_region_with_content(
        self, isolated_project: Project
    ) -> None:
        async with RaspberryMint(
            project=isolated_project,
            regional_content={Region.FRONT_PAGE_CONTENT: [ContentManufacturer(Static)]},
        ) as sut:
            assert isinstance(
                (await sut.regional_content)[Region.FRONT_PAGE_CONTENT.value][0], Static
            )

    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(
        self, isolated_app: App, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            app=isolated_app, extensions=[RaspberryMint]
        ) as project:
            await generate(project)
            assert (project.www_directory / "betty.webmanifest").is_file()
