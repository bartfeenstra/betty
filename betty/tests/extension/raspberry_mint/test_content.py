from pathlib import Path

import pytest

from betty.ancestry.citation import Citation
from betty.ancestry.enclosure import Enclosure
from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.link import Link
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.source import Source
from betty.app import App
from betty.content import (
    ContentDefinition,
    ContentManufacturer,
)
from betty.content.contents import Render, RenderConfiguration
from betty.date import Date
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.document import Document
from betty.extension.raspberry_mint import Breakpoint, JustifyContent, RaspberryMint
from betty.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.extension.raspberry_mint.content import (
    Citations,
    ColorStyle,
    ColorStyleConfiguration,
    Columns,
    ColumnsConfiguration,
    ColumnsWidth,
    Enclosees,
    EntityCard,
    ExternalLinks,
    Facts,
    Families,
    FileReferees,
    Media,
    MediaGallery,
    Presences,
    PresencesConfiguration,
    Section,
    SectionConfiguration,
    ShorthandColumnsWidth,
    Timeline,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.model.reference import EntityReference
from betty.project import Project
from betty.role.roles import Subject, Witness
from betty.test_utils.ancestry.has_citations import DummyHasCitations
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.content import NoOpContent
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestEntityCard:
    async def test_build_template(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            async with project:
                sut = await EntityCard.new(
                    project, EntityReference(entity.plugin(), entity.id)
                )

                provided_content = await sut.build(document=Document())
        assert provided_content is not None
        assert entity.public_id in provided_content


class TestSectionConfiguration(DataTestBase[SectionConfiguration]):
    sut_cls = SectionConfiguration

    def test_content(self) -> None:
        sut = SectionConfiguration(
            ContentManufacturer("my-first-content"), heading=DUMMY_LOCALIZABLE
        )
        assert sut.content[0].plugin_id == "my-first-content"

    def test_heading(self) -> None:
        heading = Plain("My First Section")
        sut = SectionConfiguration(
            ContentManufacturer("my-first-content"), heading=heading
        )
        assert sut.heading is heading

    def test_name(self) -> None:
        sut = SectionConfiguration(
            ContentManufacturer("my-first-content"),
            name="my-first-section",
            heading=DUMMY_LOCALIZABLE,
        )
        assert sut.name == "my-first-section"

    def test_visually_hide_heading(self) -> None:
        sut = SectionConfiguration(
            ContentManufacturer("my-first-content"),
            heading=DUMMY_LOCALIZABLE,
            visually_hide_heading=True,
        )
        assert sut.visually_hide_heading


class TestSection:
    async def test_build_template__without_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(
            isolated_app, plugins={ContentDefinition: [NoOpContent]}
        ) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Section.new(
                    project,
                    SectionConfiguration(
                        ContentManufacturer(NoOpContent),
                        heading="My First Section",
                    ),
                )
                assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Section.new(
                    project,
                    SectionConfiguration(
                        ContentManufacturer(
                            Render,
                            RenderConfiguration("My First Content"),
                        ),
                        heading="My First Section",
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Section" in actual
        assert "My First Content" in actual

    async def test_build_template__with_name(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Section.new(
                    project,
                    SectionConfiguration(
                        ContentManufacturer(
                            Render,
                            RenderConfiguration("My First Content"),
                        ),
                        name="my-first-section",
                        heading="My First Section",
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "my-first-section" in actual

    async def test_build_template__with_visually_hide_heading(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Section.new(
                    project,
                    SectionConfiguration(
                        ContentManufacturer(
                            Render,
                            RenderConfiguration("My First Content"),
                        ),
                        visually_hide_heading=True,
                        heading="My First Section",
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "visually-hidden" in actual


class TestFamilies:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Place(),
            Event(),
        ],
    )
    async def test_build_template__without_person(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Families.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_person(self, isolated_app: App) -> None:
        parent = Person(id="parent")
        resource = Person(id="resource", parents=[parent])
        child = Person(id="child", parents=[resource])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            project.ancestry.add(resource)
            async with project:
                sut = await Families.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert parent.public_id in actual
        assert child.public_id in actual


class TestMedia:
    async def test_build_template__without_file(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Media.new(project)
                assert await sut.build(document=Document(object())) is None

    async def test_build_template__with_file(self, isolated_app: App) -> None:
        resource = File(
            ASSETS_DIRECTORY_PATH
            / "universe"
            / "public"
            / "static"
            / "betty-16x16.png",
            media_type=MediaType("image/png"),
        )
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Media.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert resource.label.localize(DEFAULT_LOCALIZER) in actual


class TestMediaGallery:
    async def test_build_template__without_has_file_references(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                assert await sut.build(document=Document(object())) is None

    async def test_build_template__with_has_file_references_without_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_file_references_with_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        file = File(Path(__file__))
        FileReference(resource, file)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert file.label.localize(DEFAULT_LOCALIZER) in actual


class TestColorStyleConfiguration(DataTestBase[ColorStyleConfiguration]):
    sut_cls = ColorStyleConfiguration

    def test_content(self) -> None:
        sut = ColorStyleConfiguration(
            ContentManufacturer("my-first-content"), style=ColorStyleOption.DARK
        )
        assert sut.content[0].plugin_id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleConfiguration(
            ContentManufacturer("my-first-content"), style=style
        )
        assert sut.style == style


class TestColorStyle:
    async def test_build_template__without_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(
            isolated_app, plugins={ContentDefinition: [NoOpContent]}
        ) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ColorStyle.new(
                    project,
                    ColorStyleConfiguration(
                        ContentManufacturer(NoOpContent),
                        style=ColorStyleOption.DARK,
                    ),
                )
                assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ColorStyle.new(
                    project,
                    ColorStyleConfiguration(
                        ContentManufacturer(
                            Render, RenderConfiguration("My First Content")
                        ),
                        style=ColorStyleOption.DARK,
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Content" in actual


class TestExternalLinks:
    async def test_build_template__without_has_links(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                provided_content = await sut.build(document=Document(object()))
        assert provided_content is None

    async def test_build_template__with_has_links_without_links(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_links_with_links(
        self, isolated_app: App
    ) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert url in actual


class TestTimeline:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_associated_events(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_person(self, isolated_app: App) -> None:
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Person()
        Presence(resource, Subject(), event)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual

    async def test_build_template__with_place(self, isolated_app: App) -> None:
        enclosee_event = Event(id="E0", date=Date(1970, 1, 1))
        enclosee = Place(events=[enclosee_event])
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Place(events=[event])
        Enclosure(enclosee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual
        assert enclosee_event.public_id in actual


class TestFacts:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_associated_facts(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Facts.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_citation(self, isolated_app: App) -> None:
        resource = Citation(source=Source())
        fact = DummyHasCitations(citations=[resource])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Facts.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual

    async def test_build_template__with_source(self, isolated_app: App) -> None:
        resource = Source()
        citation = Citation(source=resource)
        fact = DummyHasCitations(citations=[citation])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Facts.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual


class TestPresencesConfiguration(DataTestBase[PresencesConfiguration]):
    sut_cls = PresencesConfiguration

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


class TestPresences:
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
    async def test_build_template__without_presences(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = Presences(jinja=await project.jinja)
                assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_presences(self, isolated_app: App) -> None:
        person = Person(id="P1")
        resource = Event()
        Presence(person, Subject(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = Presences(jinja=await project.jinja)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person.public_id in actual

    async def test_build_template__with_presences_with_include(
        self, isolated_app: App
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = Presences(include=[Subject], jinja=await project.jinja)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual

    async def test_build_template__with_presences_with_exclude(
        self, isolated_app: App
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Presences.new(
                    project, PresencesConfiguration(exclude=[Witness])
                )
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual


class TestColumnsConfiguration(DataTestBase[ColumnsConfiguration]):
    sut_cls = ColumnsConfiguration

    def test_content(self) -> None:
        content = ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))
        sut = ColumnsConfiguration([content])
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
                [[ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))]],
                width=width,
            ).width
            == expected
        )

    def test_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration(
            [[ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))]],
            justify_content=justify_content,
        )
        assert sut.justify_content == justify_content


class TestColumns:
    async def test_build_template__minimal(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Columns.new(
                    project,
                    ColumnsConfiguration(
                        [
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ]
                        ]
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12" in actual

    async def test_build_template__single_column_multiple_breakpoints(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Columns.new(
                    project,
                    ColumnsConfiguration(
                        [
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ]
                        ],
                        width={Breakpoint.XS: 12, Breakpoint.LG: 6},
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12 col-lg-6" in actual

    async def test_build_template__multiple_columns_single_breakpoint(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Columns.new(
                    project,
                    ColumnsConfiguration(
                        [
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ],
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ],
                        ],
                        width=[8, 4],
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8" in actual
        assert "col col-4" in actual

    async def test_build_template__multiple_columns_multiple_breakpoints(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Columns.new(
                    project,
                    ColumnsConfiguration(
                        [
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ],
                            [
                                ContentManufacturer(
                                    Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                                )
                            ],
                        ],
                        width={Breakpoint.XS: [8, 4], Breakpoint.LG: [7, 5]},
                    ),
                )
                actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8 col-lg-7" in actual
        assert "col col-4 col-lg-5" in actual


class TestEnclosees:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_enclosees(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Enclosees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_enclosee(self, isolated_app: App) -> None:
        enclosee = Place()
        resource = Place()
        Enclosure(enclosee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Enclosees.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert enclosee.public_id in actual


class TestFileReferees:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            File(Path(__file__)),
        ],
    )
    async def test_build_template__without_referees(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await FileReferees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_referee(self, isolated_app: App) -> None:
        referee = DummyHasFileReferences()
        resource = File(Path(__file__))
        FileReference(referee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await FileReferees.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert referee.public_id in actual


class TestCitations:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            DummyHasCitations(),
        ],
    )
    async def test_build_template__without_citations(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await project.factory.new(Citations)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_citation(self, isolated_app: App) -> None:
        citation = Citation(source=Source())
        resource = DummyHasCitations(citations=[citation])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await project.factory.new(Citations)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert 'href="#reference-1"' in actual
