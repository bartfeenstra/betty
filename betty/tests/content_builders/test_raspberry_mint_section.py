from betty.content_builder import NewContentBuilder
from betty.content_builders.raspberry_mint_section import Section, SectionConfig
from betty.content_builders.render import Render, RenderConfig
from betty.content_builders.static import Static
from betty.document import Document
from betty.localizables.plain import Plain
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestSectionData(DataTestBase[SectionConfig]):
    sut_cls = SectionConfig

    def test_content(self) -> None:
        sut = SectionConfig(NewContentBuilder("my-first-content"), heading="-")
        assert sut.content[0].id == "my-first-content"

    def test_heading(self) -> None:
        heading = Plain("My First Section")
        sut = SectionConfig(NewContentBuilder("my-first-content"), heading=heading)
        assert sut.heading is heading

    def test_name(self) -> None:
        sut = SectionConfig(
            NewContentBuilder("my-first-content"),
            name="my-first-section",
            heading="-",
        )
        assert sut.name == "my-first-section"

    def test_visually_hide_heading(self) -> None:
        sut = SectionConfig(
            NewContentBuilder("my-first-content"),
            heading="-",
            visually_hide_heading=True,
        )
        assert sut.visually_hide_heading


class TestSection:
    async def test_build_template__without_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Section]) as project:
            sut = await Section.new(
                project,
                SectionConfig(
                    NewContentBuilder(Static),
                    heading="My First Section",
                ),
            )
            assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Section]) as project:
            sut = await Section.new(
                project,
                SectionConfig(
                    NewContentBuilder(
                        Render,
                        RenderConfig("My First Content"),
                    ),
                    heading="My First Section",
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Section" in actual
        assert "My First Content" in actual

    async def test_build_template__with_name(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Section]) as project:
            sut = await Section.new(
                project,
                SectionConfig(
                    NewContentBuilder(
                        Render,
                        RenderConfig("My First Content"),
                    ),
                    name="my-first-section",
                    heading="My First Section",
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "my-first-section" in actual

    async def test_build_template__with_visually_hide_heading(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Section]) as project:
            sut = await Section.new(
                project,
                SectionConfig(
                    NewContentBuilder(
                        Render,
                        RenderConfig("My First Content"),
                    ),
                    visually_hide_heading=True,
                    heading="My First Section",
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "visually-hidden" in actual
