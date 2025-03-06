from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.model import ENTITY_TYPE_REPOSITORY, Entity
from betty.model.config import EntityReference
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.config import EntityTypeConfiguration
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.generate import generate
from betty.test_utils.model import DummyUserFacingEntity
from betty.test_utils.project.extension import ExtensionTestBase
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from betty.app import App


class TestRaspberryMint(EntryPointProviderTestBase, ExtensionTestBase[RaspberryMint]):
    @override
    def get_sut_class(self) -> type[RaspberryMint]:
        return RaspberryMint

    async def test_filters(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.filters)

    async def test_public_css_paths(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            assert len(sut.public_css_paths)

    async def test_bootstrap__should_validate_featured_entities_configuration(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await RaspberryMint.new_for_project(project)
            sut.configuration.featured_entities.replace(
                EntityReference("non-existent-entity")
            )
            with pytest.raises(AssertionFailed):
                async with sut:
                    pass  # pragma: nocover

    async def test_generate_html_list__for_third_party_entity(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=ProxyPluginRepository[Entity](
                StaticPluginRepository(DummyUserFacingEntity), ENTITY_TYPE_REPOSITORY
            ),
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.entity_types.replace(
                EntityTypeConfiguration(DummyUserFacingEntity, generate_html_list=True)
            )
            async with project:
                await generate(project)
            assert (
                project.configuration.www_directory_path
                / DummyUserFacingEntity.plugin_id()
                / "index.html"
            ).is_file()
