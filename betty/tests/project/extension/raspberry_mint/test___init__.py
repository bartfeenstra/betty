from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.exception import UserFacingException
from betty.model import ENTITY_TYPE_REPOSITORY, EntityDefinition
from betty.model.config import EntityReference
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.config import EntityTypeConfiguration
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.generate import generate
from betty.test_utils.model import DummyUserFacingEntityOne
from betty.test_utils.project.extension.webpack.build import EntryPointProviderTestBase

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App
    from betty.project.extension import Extension


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

    async def test_generate__html_list_for_third_party_entity(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=ProxyPluginRepository(
                EntityDefinition,
                StaticPluginRepository(
                    EntityDefinition, DummyUserFacingEntityOne.plugin
                ),
                ENTITY_TYPE_REPOSITORY,
            ),
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.configuration.entity_types.replace(
                EntityTypeConfiguration(
                    DummyUserFacingEntityOne, generate_html_list=True
                )
            )
            async with project:
                await generate(project)
            assert (
                project.configuration.www_directory_path
                / DummyUserFacingEntityOne.plugin.id
                / "index.html"
            ).is_file()
