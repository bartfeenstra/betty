from typing import TYPE_CHECKING

import pytest

from betty.ancestry.person import Person
from betty.app import App
from betty.exception import HumanFacingException
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model.config import EntityReference
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.content_provider import (
    FeaturedEntities,
    Section,
    SectionConfiguration,
)
from betty.resource import new_context

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.content_provider import ContentProvider, ContentProviderDefinition


class TestFeaturedEntities:
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
        sut = SectionConfiguration(name="", heading="My First Section")
        assert sut.heading.localize(DEFAULT_LOCALIZER) == "My First Section"

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


class TestSection:
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
                        "plain-text", configuration="My First Content"
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
                        "plain-text", configuration="My First Content"
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
                        "plain-text", configuration="My First Content"
                    )
                )
                actual = await sut.provide(resource=new_context())
                assert actual is not None
                assert "visually-hidden" in actual
