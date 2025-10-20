from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.exception import UserFacingException
from betty.model import EntityDefinition
from betty.model.config import EntityReference
from betty.plugin.static import StaticPluginRepository
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
    from betty.test_utils.conftest import NewTemporaryAppFactory


class TestRaspberryMint(EntryPointProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, new_temporary_app: App) -> Extension:
        async with Project.new_temporary(new_temporary_app) as project, project:
            return await RaspberryMint.new_for_project(project)

    async def test_filters(self, sut: RaspberryMint) -> None:
        assert sut.filters

    async def test_bootstrap__should_validate_featured_entities_configuration(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await RaspberryMint.new_for_project(project)
            sut.configuration.featured_entities.replace(
                EntityReference("non-existent-entity")
            )
            with pytest.raises(UserFacingException):
                async with sut:
                    pass  # pragma: nocover

    @check_skip_webpack_entry_point_provider
    async def test_generate__html_list_for_third_party_entity(
        self, new_temporary_app_factory: NewTemporaryAppFactory
    ) -> None:
        async with (
            new_temporary_app_factory(
                entity_type_repository=StaticPluginRepository(
                    EntityDefinition, DummyEntityOne.plugin
                )
            ) as app,
            app,
            Project.new_temporary(app) as project,
        ):
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
