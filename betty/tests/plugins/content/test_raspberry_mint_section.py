from betty.app import App
from betty.content import ContentDefinition, ContentManufacturer
from betty.document import Document
from betty.locale.localizable.plain import Plain
from betty.plugins.content.raspberry_mint_section import Section, SectionConfiguration
from betty.plugins.content.render import Render, RenderConfiguration
from betty.plugins.content.static import Static
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


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
            isolated_app, plugins={ContentDefinition: [Static]}
        ) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Section.new(
                    project,
                    SectionConfiguration(
                        ContentManufacturer(Static),
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
