from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.link import Link
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.app import App
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider.content_providers import PlainText, PlainTextConfiguration
from betty.exception import HumanFacingException
from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.content_provider import (
    ColorStyle,
    ColorStyleConfiguration,
    ExternalLinks,
    Family,
    FeaturedEntities,
    Media,
    Section,
    SectionConfiguration,
)
from betty.resource import new_context
from betty.test_utils.config.factory import ConfigurationDependentSelfFactoryTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.content_provider import ContentProvider, ContentProviderDefinition


class TestFeaturedEntities(
    ConfigurationDependentSelfFactoryTestBase[EntityReferenceSequence]
):
    @override
    @pytest.fixture
    async def configuration_dependent_self_factory_sut(
        self,
    ) -> type[ConfigurationDependentSelfFactory[EntityReferenceSequence]]:
        return FeaturedEntities

    @override
    @pytest.fixture
    def configuration_dependent_self_factory_sut_configuration(
        self,
    ) -> EntityReferenceSequence:
        return EntityReferenceSequence()

    async def test_provide__without_entities(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                assert await sut.provide(resource=new_context()) is None

    async def test_provide__with_entities(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                sut.configuration.append(EntityReference(entity.plugin, entity.id))
                provided_content = await sut.provide(resource=new_context())
        assert provided_content is not None
        assert entity.public_id in provided_content


class TestSectionConfiguration:
    def test_content(self) -> None:
        content: Sequence[
            PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
        ] = [PluginInstanceConfiguration("my-first-content")]
        sut = SectionConfiguration(name="", heading="", content=content)
        assert sut.content[0].id == "my-first-content"

    def test_heading(self) -> None:
        heading = Plain("My First Section")
        sut = SectionConfiguration(name="", heading=heading)
        assert sut.heading is heading

    def test_name(self) -> None:
        sut = SectionConfiguration(name="my-first-section", heading="")
        assert sut.name == "my-first-section"

    def test_load__minimal(self) -> None:
        sut = SectionConfiguration(name="", heading="")
        sut.load(
            {
                "heading": "My First Section",
                "content": ["my-first-content"],
            }
        )
        assert sut.heading.localize(DEFAULT_LOCALIZER) == "My First Section"
        assert sut.content[0].id == "my-first-content"

    def test_load__with_name(self) -> None:
        sut = SectionConfiguration(name="", heading="")
        sut.load(
            {
                "name": "my-first-section",
                "heading": "My First Section",
                "content": ["my-first-content"],
            }
        )
        assert sut.name == "my-first-section"

    def test_load__without_heading(self) -> None:
        sut = SectionConfiguration(name="", heading="")
        with pytest.raises(HumanFacingException):
            sut.load(
                {
                    "name": "my-first-section",
                    "content": ["my-first-content"],
                }
            )

    def test_load__without_content(self) -> None:
        sut = SectionConfiguration(name="", heading="")
        with pytest.raises(HumanFacingException):
            sut.load(
                {
                    "name": "my-first-section",
                    "heading": "My First Section",
                }
            )

    def test_dump__minimal(self) -> None:
        sut = SectionConfiguration(name="my-first-section", heading="My First Section")
        assert sut.dump() == {
            "name": "my-first-section",
            "heading": "My First Section",
            "content": [],
        }

    def test_dump__full(self) -> None:
        sut = SectionConfiguration(
            name="my-first-section",
            heading="My First Section",
            content=[PluginInstanceConfiguration("my-first-content")],
        )
        assert sut.dump() == {
            "name": "my-first-section",
            "heading": "My First Section",
            "content": [
                "my-first-content",
            ],
        }

    def test_get_mutables__minimal(self) -> None:
        sut = SectionConfiguration(heading="My First Section")
        assert list(sut.get_mutables())

    def test_get_mutables__with_content(self) -> None:
        sut = SectionConfiguration(
            heading="My First Section",
            content=[PluginInstanceConfiguration("my-first-content")],
        )
        assert list(sut.get_mutables())


class TestSection(ConfigurationDependentSelfFactoryTestBase[SectionConfiguration]):
    @override
    @pytest.fixture
    async def configuration_dependent_self_factory_sut(
        self,
    ) -> type[ConfigurationDependentSelfFactory[SectionConfiguration]]:
        return Section

    @override
    @pytest.fixture
    def configuration_dependent_self_factory_sut_configuration(
        self,
    ) -> SectionConfiguration:
        return SectionConfiguration(heading="")

    async def test_provide__without_content(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
            assert await sut.provide(resource=new_context()) is None

    async def test_provide__with_content(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.heading = "My First Section"
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        "plain-text", PlainTextConfiguration("My First Content")
                    )
                )
                actual = await sut.provide(resource=new_context())
        assert actual is not None
        assert "My First Section" in actual
        assert "My First Content" in actual

    async def test_provide__with_name(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.name = "my-first-section"
                sut.configuration.heading = "My First Section"
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        "plain-text", PlainTextConfiguration("My First Content")
                    )
                )
                actual = await sut.provide(resource=new_context())
        assert actual is not None
        assert "my-first-section" in actual

    async def test_provide__with_visually_hide_heading(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.heading = "My First Section"
                sut.configuration.visually_hide_heading = True
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        "plain-text", PlainTextConfiguration("My First Content")
                    )
                )
                actual = await sut.provide(resource=new_context())
        assert actual is not None
        assert "visually-hidden" in actual


class TestFamily:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Place(),
            Event(),
        ],
    )
    async def test_provide__without_person(
        self, resource: object, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Family.new_for_project(project)
        assert await sut.provide(resource=new_context(resource)) is None

    async def test_provide__with_person(self, temporary_app: App) -> None:
        parent = Person(id="parent")
        resource = Person(id="resource", parents=[parent])
        child = Person(id="child", parents=[resource])
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.ancestry.add(resource)
            async with project:
                sut = await Family.new_for_project(project)
                actual = await sut.provide(resource=new_context(resource))
        assert actual is not None
        assert parent.public_id in actual
        assert child.public_id in actual


class TestMedia:
    async def test_provide__without_has_file_references(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Media.new_for_project(project)
                assert await sut.provide(resource=new_context(object())) is None

    async def test_provide__with_has_file_references_without_file_references(
        self, temporary_app: App
    ) -> None:
        resource = Person()
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Media.new_for_project(project)
                assert await sut.provide(resource=new_context(resource)) is None

    async def test_provide__with_has_file_references_with_file_references(
        self, temporary_app: App
    ) -> None:
        resource = Person()
        file = File(Path(__file__))
        FileReference(resource, file)
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Media.new_for_project(project)
                actual = await sut.provide(resource=new_context(resource))
        assert actual is not None
        assert file.label.localize(DEFAULT_LOCALIZER) in actual


class TestColorStyleConfiguration:
    def test_content(self) -> None:
        content: Sequence[
            PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
        ] = [PluginInstanceConfiguration("my-first-content")]
        sut = ColorStyleConfiguration(content=content)
        assert sut.content[0].id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleConfiguration(style=style)
        assert sut.style == style

    def test_load__minimal(self) -> None:
        sut = ColorStyleConfiguration()
        sut.load(
            {
                "content": ["my-first-content"],
            }
        )
        assert sut.content[0].id == "my-first-content"

    def test_load__with_style(self) -> None:
        sut = ColorStyleConfiguration()
        sut.load(
            {
                "style": "dark-secondary",
                "content": ["my-first-content"],
            }
        )
        assert sut.style is ColorStyleOption.DARK_SECONDARY

    def test_load__without_content(self) -> None:
        sut = ColorStyleConfiguration()
        with pytest.raises(HumanFacingException):
            sut.load({})

    def test_dump(self) -> None:
        sut = ColorStyleConfiguration(
            content=[PluginInstanceConfiguration("my-first-content")],
            style=ColorStyleOption.DARK_SECONDARY,
        )
        assert sut.dump() == {
            "style": "dark-secondary",
            "content": [
                "my-first-content",
            ],
        }

    def test_get_mutables__minimal(self) -> None:
        sut = ColorStyleConfiguration()
        assert not list(sut.get_mutables())

    def test_get_mutables__with_content(self) -> None:
        sut = ColorStyleConfiguration(
            content=[PluginInstanceConfiguration("my-first-content")]
        )
        assert list(sut.get_mutables())


class TestColorStyle:
    async def test_provide__without_content(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ColorStyle.new_for_project(project)
                assert await sut.provide(resource=new_context()) is None

    async def test_provide__with_content(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ColorStyle.new_for_project(project)
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        PlainText, PlainTextConfiguration("My First Content")
                    )
                )
                actual = await sut.provide(resource=new_context())
        assert actual is not None
        assert "My First Content" in actual


class TestExternalLinks:
    async def test_provide__without_has_links(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                provided_content = await sut.provide(resource=new_context(object()))
        assert provided_content is None

    async def test_provide__with_has_links_without_links(
        self, temporary_app: App
    ) -> None:
        resource = Person()
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                assert await sut.provide(resource=new_context(resource)) is None

    async def test_provide__with_has_links_with_links(self, temporary_app: App) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                actual = await sut.provide(resource=new_context(resource))
        assert actual is not None
        assert url in actual
