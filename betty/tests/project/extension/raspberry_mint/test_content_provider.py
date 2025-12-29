from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.link import Link
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.ancestry.source import Source
from betty.app import App
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider
from betty.content_provider.content_providers import Render, RenderConfiguration
from betty.date import Date
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.document import Document
from betty.exception import HumanFacingException
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.media_type.media_types import PLAIN_TEXT
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
    PluginInstanceConfigurationSequenceSequence,
)
from betty.plugin.repository.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension.raspberry_mint import (
    Breakpoint,
    JustifyContent,
    RaspberryMint,
)
from betty.project.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.project.extension.raspberry_mint.content_provider import (
    ColorStyle,
    ColorStyleConfiguration,
    Columns,
    ColumnsConfiguration,
    ColumnsWidth,
    Enclosees,
    ExternalLinks,
    Facts,
    Families,
    FeaturedEntities,
    Media,
    MediaGallery,
    Presences,
    PresencesConfiguration,
    Section,
    SectionConfiguration,
    ShorthandColumnsWidth,
    Timeline,
)
from betty.test_utils.ancestry.has_citations import DummyHasCitations
from betty.test_utils.config.factory import ConfigurationDependentSelfFactoryTestBase
from betty.test_utils.content_provider import ContentProviderTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.content_provider import ContentProviderDefinition
    from betty.serde.dump import Dump


class TestFeaturedEntities(
    ConfigurationDependentSelfFactoryTestBase[EntityReferenceSequence],
    ContentProviderTestBase,
):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return FeaturedEntities(
                jinja2_environment=await project.jinja2_environment, project=project
            )

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

    async def test_provide__without_entities(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                assert await sut.provide(document=Document()) is None

    async def test_provide__with_entities(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                sut.configuration.append(EntityReference(entity.plugin(), entity.id))
                provided_content = await sut.provide(document=Document())
        assert provided_content is not None
        assert entity.public_id in provided_content


class TestSectionConfiguration:
    def test_content(self) -> None:
        content: Sequence[
            PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
        ] = [PluginInstanceConfiguration("my-first-content")]
        sut = SectionConfiguration(name="", heading=DUMMY_LOCALIZABLE, content=content)
        assert sut.content[0].id == "my-first-content"

    def test_heading(self) -> None:
        heading = Plain("My First Section")
        sut = SectionConfiguration(name="", heading=heading)
        assert sut.heading is heading

    def test_name(self) -> None:
        sut = SectionConfiguration(name="my-first-section", heading=DUMMY_LOCALIZABLE)
        assert sut.name == "my-first-section"

    def test_load__minimal(self) -> None:
        sut = SectionConfiguration.load(
            {
                "heading": "My First Section",
                "content": ["my-first-content"],
            }
        )
        assert sut.heading.localize(DEFAULT_LOCALIZER) == "My First Section"
        assert sut.content[0].id == "my-first-content"

    def test_load__with_name(self) -> None:
        sut = SectionConfiguration.load(
            {
                "name": "my-first-section",
                "heading": "My First Section",
                "content": ["my-first-content"],
            }
        )
        assert sut.name == "my-first-section"

    def test_load__without_heading(self) -> None:
        with pytest.raises(HumanFacingException):
            SectionConfiguration.load(
                {
                    "name": "my-first-section",
                    "content": ["my-first-content"],
                }
            )

    def test_load__without_content(self) -> None:
        with pytest.raises(HumanFacingException):
            SectionConfiguration.load(
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


class TestSection(
    ConfigurationDependentSelfFactoryTestBase[SectionConfiguration],
    ContentProviderTestBase,
):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Section(jinja2_environment=await project.jinja2_environment)

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
        return SectionConfiguration(heading=DUMMY_LOCALIZABLE)

    async def test_provide__without_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                assert await sut.provide(document=Document()) is None

    async def test_provide__with_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.heading = "My First Section"
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        Render,
                        RenderConfiguration("My First Content"),
                    )
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "My First Section" in actual
        assert "My First Content" in actual

    async def test_provide__with_name(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.name = "my-first-section"
                sut.configuration.heading = "My First Section"
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        Render,
                        RenderConfiguration("My First Content"),
                    )
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "my-first-section" in actual

    async def test_provide__with_visually_hide_heading(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Section.new_for_project(project)
                sut.configuration.heading = "My First Section"
                sut.configuration.visually_hide_heading = True
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        Render,
                        RenderConfiguration("My First Content"),
                    )
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "visually-hidden" in actual


class TestFamilies(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Families(jinja2_environment=await project.jinja2_environment)

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
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Families.new_for_project(project)
        assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_person(self, isolated_app: App) -> None:
        parent = Person(id="parent")
        resource = Person(id="resource", parents=[parent])
        child = Person(id="child", parents=[resource])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            project.ancestry.add(resource)
            async with project:
                sut = await Families.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert parent.public_id in actual
        assert child.public_id in actual


class TestMedia(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Media(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_file(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Media.new_for_project(project)
                assert await sut.provide(document=Document(object())) is None

    async def test_provide__with_file(self, isolated_app: App) -> None:
        resource = File(
            ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-16x16.png",
            media_type=MediaType("image/png"),
        )
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Media.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert resource.label.localize(DEFAULT_LOCALIZER) in actual


class TestMediaGallery(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return MediaGallery(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_has_file_references(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await MediaGallery.new_for_project(project)
                assert await sut.provide(document=Document(object())) is None

    async def test_provide__with_has_file_references_without_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await MediaGallery.new_for_project(project)
                assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_has_file_references_with_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        file = File(Path(__file__))
        FileReference(resource, file)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await MediaGallery.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
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
        sut = ColorStyleConfiguration.load(
            {
                "content": ["my-first-content"],
            }
        )
        assert sut.content[0].id == "my-first-content"

    def test_load__with_style(self) -> None:
        sut = ColorStyleConfiguration.load(
            {
                "style": "dark-secondary",
                "content": ["my-first-content"],
            }
        )
        assert sut.style is ColorStyleOption.DARK_SECONDARY

    def test_load__without_content(self) -> None:
        with pytest.raises(HumanFacingException):
            ColorStyleConfiguration.load({})

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


class TestColorStyle(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return ColorStyle(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ColorStyle.new_for_project(project)
                assert await sut.provide(document=Document()) is None

    async def test_provide__with_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ColorStyle.new_for_project(project)
                sut.configuration.content.append(
                    PluginInstanceConfiguration(
                        Render, RenderConfiguration("My First Content")
                    )
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "My First Content" in actual


class TestExternalLinks(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return ExternalLinks(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_has_links(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                provided_content = await sut.provide(document=Document(object()))
        assert provided_content is None

    async def test_provide__with_has_links_without_links(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_has_links_with_links(self, isolated_app: App) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert url in actual


class TestTimeline(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Timeline(jinja2_environment=await project.jinja2_environment)

    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_provide__without_associated_events(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Timeline.new_for_project(project)
        assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_person(self, isolated_app: App) -> None:
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Person()
        Presence(resource, Subject(), event)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Timeline.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual

    async def test_provide__with_place(self, isolated_app: App) -> None:
        enclosee_event = Event(id="E0", date=Date(1970, 1, 1))
        enclosee = Place(events=[enclosee_event])
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Place(events=[event])
        Enclosure(enclosee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Timeline.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual
        assert enclosee_event.public_id in actual


class TestFacts(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Facts(jinja2_environment=await project.jinja2_environment)

    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_provide__without_associated_facts(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Facts.new_for_project(project)
        assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_citation(self, isolated_app: App) -> None:
        resource = Citation(source=Source())
        fact = DummyHasCitations(citations=[resource])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Facts.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual

    async def test_provide__with_source(self, isolated_app: App) -> None:
        resource = Source()
        citation = Citation(source=resource)
        fact = DummyHasCitations(citations=[citation])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Facts.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual


class TestPresencesConfiguration:
    def test_include(self) -> None:
        include = ["foo"]
        sut = PresencesConfiguration(include=include)
        assert sut.include is not None
        assert list(sut.include) == include

    def test_exclude(self) -> None:
        exclude = ["foo"]
        sut = PresencesConfiguration(exclude=exclude)
        assert sut.exclude is not None
        assert list(sut.exclude) == exclude

    def test_load__with_include(self) -> None:
        include: Dump = ["foo"]
        sut = PresencesConfiguration.load(
            {
                "include": include,
            }
        )
        assert sut.include is not None
        assert list(sut.include) == include

    def test_load__with_exclude(self) -> None:
        exclude: Dump = ["foo"]
        sut = PresencesConfiguration.load(
            {
                "exclude": exclude,
            }
        )
        assert sut.exclude is not None
        assert list(sut.exclude) == exclude

    def test_dump__minimal(self) -> None:
        sut = PresencesConfiguration()
        assert sut.dump() == {}

    def test_dump__with_include(self) -> None:
        include = ["foo"]
        sut = PresencesConfiguration(include=include)
        assert sut.dump() == {
            "include": include,
        }

    def test_dump__with_exclude(self) -> None:
        exclude = ["foo"]
        sut = PresencesConfiguration(exclude=exclude)
        assert sut.dump() == {
            "exclude": exclude,
        }


class TestPresences(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Presences(
                jinja2_environment=await project.jinja2_environment,
                presence_roles=StaticPluginRepository(PresenceRoleDefinition, Subject),
            )

    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            Event(),
        ],
    )
    async def test_provide__without_presences(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Presences(
                    jinja2_environment=await project.jinja2_environment,
                    presence_roles=StaticPluginRepository(
                        PresenceRoleDefinition, Subject
                    ),
                )
                assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_presences(self, isolated_app: App) -> None:
        person = Person(id="P1")
        resource = Event()
        Presence(person, Subject(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Presences(
                    jinja2_environment=await project.jinja2_environment,
                    presence_roles=StaticPluginRepository(
                        PresenceRoleDefinition, Subject
                    ),
                )
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert person.public_id in actual

    async def test_provide__with_presences_with_include(
        self, isolated_app: App
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Presences(
                    configuration=PresencesConfiguration(include=[Subject]),
                    jinja2_environment=await project.jinja2_environment,
                    presence_roles=StaticPluginRepository(
                        PresenceRoleDefinition, Subject
                    ),
                )
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual

    async def test_provide__with_presences_with_exclude(
        self, isolated_app: App
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Presences(
                    configuration=PresencesConfiguration(exclude=[Witness]),
                    jinja2_environment=await project.jinja2_environment,
                    presence_roles=StaticPluginRepository(
                        PresenceRoleDefinition, Subject
                    ),
                )
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual


class TestColumnsConfiguration:
    def test_content__with_single_configuration(self) -> None:
        content: PluginInstanceConfiguration[
            ContentProviderDefinition, ContentProvider
        ] = PluginInstanceConfiguration(Render, RenderConfiguration(DUMMY_LOCALIZABLE))
        sut = ColumnsConfiguration(
            content=PluginInstanceConfigurationSequenceSequence(
                [PluginInstanceConfigurationSequence([content])]
            )
        )
        assert list(map(list, sut.content)) == [[content]]

    def test_content__with_multiple_configurations(self) -> None:
        content: PluginInstanceConfiguration[
            ContentProviderDefinition, ContentProvider
        ] = PluginInstanceConfiguration(Render, RenderConfiguration(DUMMY_LOCALIZABLE))
        sut = ColumnsConfiguration(
            content=PluginInstanceConfigurationSequenceSequence(
                [PluginInstanceConfigurationSequence([content])]
            )
        )
        assert list(map(list, sut.content)) == [[content]]

    @pytest.mark.parametrize(
        ("expected", "width"),
        [
            ({Breakpoint.XS: [7]}, 7),
            ({Breakpoint.XS: [7]}, [7]),
            ({Breakpoint.XS: [7]}, {Breakpoint.XS: 7}),
            ({Breakpoint.XS: [7]}, {Breakpoint.XS: [7]}),
        ],
    )
    def test_width(self, expected: ColumnsWidth, width: ShorthandColumnsWidth) -> None:
        assert (
            ColumnsConfiguration(
                width=width,
                content=PluginInstanceConfiguration(
                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                ),
            ).width
            == expected
        )

    def test_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration(
            content=PluginInstanceConfiguration(
                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
            ),
            justify_content=justify_content,
        )
        assert sut.justify_content == justify_content

    def test_load__minimal(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration.load(
            {
                "content": [
                    [
                        {
                            "id": "render",
                            "configuration": {
                                "content": "DUMMY_LOCALIZABLE",
                                "media_type": str(PLAIN_TEXT),
                            },
                        }
                    ]
                ],
                "justify_content": justify_content.value,
            }
        )
        assert len(sut.content) == 1
        assert sut.content[0][0].id == "render"
        assert isinstance(sut.content[0][0].configuration, Mapping)
        assert sut.content[0][0].configuration["content"] == "DUMMY_LOCALIZABLE"
        assert sut.content[0][0].configuration["media_type"] == str(PLAIN_TEXT)

    def test_load__with_width(self) -> None:
        sut = ColumnsConfiguration.load(
            {
                "content": [
                    [
                        {
                            "id": "render",
                            "configuration": {
                                "content": "DUMMY_LOCALIZABLE",
                                "media_type": str(PLAIN_TEXT),
                            },
                        }
                    ]
                ],
                "width": {Breakpoint.XS.value: [1, 2, 3]},
            }
        )
        assert sut.width == {Breakpoint.XS: [1, 2, 3]}

    def test_load__with_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration.load(
            {
                "content": [
                    [
                        {
                            "id": "render",
                            "configuration": {
                                "content": "DUMMY_LOCALIZABLE",
                                "media_type": str(PLAIN_TEXT),
                            },
                        }
                    ]
                ],
                "justify_content": justify_content.value,
            }
        )
        assert sut.justify_content == justify_content

    def test_dump__minimal(self) -> None:
        sut = ColumnsConfiguration(
            content=PluginInstanceConfiguration(
                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
            )
        )
        assert sut.dump() == {
            "content": [
                [
                    {
                        "id": "render",
                        "configuration": {
                            "content": "DUMMY_LOCALIZABLE",
                            "media_type": str(PLAIN_TEXT),
                        },
                    },
                ]
            ],
            "width": {
                "xs": [12],
            },
        }

    def test_dump__with_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration(
            content=PluginInstanceConfiguration(
                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
            ),
            justify_content=justify_content,
        )
        actual = sut.dump()
        assert isinstance(actual, Mapping)
        assert "justify_content" in actual
        assert actual["justify_content"] == justify_content.value


class TestColumns(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Columns(
                configuration=ColumnsConfiguration(
                    content=PluginInstanceConfiguration(
                        Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                    )
                ),
                jinja2_environment=await project.jinja2_environment,
            )

    async def test_provide__minimal(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Columns(
                    configuration=ColumnsConfiguration(
                        content=PluginInstanceConfiguration(
                            Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                        )
                    ),
                    jinja2_environment=await project.jinja2_environment,
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "col col-12" in actual

    async def test_provide__single_column_multiple_breakpoints(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Columns(
                    configuration=ColumnsConfiguration(
                        content=PluginInstanceConfiguration(
                            Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                        ),
                        width={Breakpoint.XS: 12, Breakpoint.LG: 6},
                    ),
                    jinja2_environment=await project.jinja2_environment,
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "col col-12 col-lg-6" in actual

    async def test_provide__multiple_columns_single_breakpoint(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Columns(
                    configuration=ColumnsConfiguration(
                        content=PluginInstanceConfigurationSequenceSequence(
                            [
                                PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(
                                            Render,
                                            RenderConfiguration(DUMMY_LOCALIZABLE),
                                        ),
                                    ]
                                ),
                                PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(
                                            Render,
                                            RenderConfiguration(DUMMY_LOCALIZABLE),
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        width=[8, 4],
                    ),
                    jinja2_environment=await project.jinja2_environment,
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "col col-8" in actual
        assert "col col-4" in actual

    async def test_provide__multiple_columns_multiple_breakpoints(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = Columns(
                    configuration=ColumnsConfiguration(
                        content=PluginInstanceConfigurationSequenceSequence(
                            [
                                PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(
                                            Render,
                                            RenderConfiguration(DUMMY_LOCALIZABLE),
                                        ),
                                    ]
                                ),
                                PluginInstanceConfigurationSequence(
                                    [
                                        PluginInstanceConfiguration(
                                            Render,
                                            RenderConfiguration(DUMMY_LOCALIZABLE),
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        width={Breakpoint.XS: [8, 4], Breakpoint.LG: [7, 5]},
                    ),
                    jinja2_environment=await project.jinja2_environment,
                )
                actual = await sut.provide(document=Document())
        assert actual is not None
        assert "col col-8 col-lg-7" in actual
        assert "col col-4 col-lg-5" in actual


class TestEnclosees(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Enclosees(jinja2_environment=await project.jinja2_environment)

    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_provide__without_enclosees(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Enclosees.new_for_project(project)
        assert await sut.provide(document=Document(resource)) is None

    async def test_provide__with_enclosee(self, isolated_app: App) -> None:
        enclosee = Place()
        resource = Place()
        Enclosure(enclosee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await Enclosees.new_for_project(project)
                actual = await sut.provide(document=Document(resource))
        assert actual is not None
        assert enclosee.public_id in actual
