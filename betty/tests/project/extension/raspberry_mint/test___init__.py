from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.model import EntityDefinition
from betty.project import Project
from betty.project.config import EntityTypeConfiguration
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.generate import generate
from betty.test_utils.model import DummyEntityOne
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase
from betty.tests.conftest import check_skip_webpack_entry_point_provider

if TYPE_CHECKING:
    from betty.app import App
    from betty.project.extension import Extension


class TestRaspberryMint(EntryPointProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, temporary_app: App) -> Extension:
        async with Project.new_temporary(temporary_app) as project, project:
            return await RaspberryMint.new_for_project(project)

    async def test_filters(self, sut: RaspberryMint) -> None:
        assert sut.filters

    async def test_bootstrap__should_validate_featured_entities_configuration(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await RaspberryMint.new_for_project(project)
            sut.configuration.regional_content["unknown-region"] = []
            with pytest.raises(HumanFacingException) as exc_info:
                async with sut:
                    pass  # pragma: nocover
        assert (
            'data["extensions"]["raspberry-mint"]["regional_content"]["unknown-region"]'
            in str(exc_info.value)
        )

    @check_skip_webpack_entry_point_provider
    async def test_generate__html_list_for_third_party_entity(
        self, temporary_app: App
    ) -> None:
        with EntityDefinition.type.override_discoveries(DummyEntityOne.plugin):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(RaspberryMint)
                project.configuration.entity_types.replace(
                    EntityTypeConfiguration(DummyEntityOne, generate_html_list=True)
                )
                async with project:
                    await generate(project)
                assert (
                    project.configuration.www_directory_path
                    / DummyEntityOne.plugin.id
                    / "index.html"
                ).is_file()

    async def test_regions(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await RaspberryMint.new_for_project(project)
            assert sut.regions
