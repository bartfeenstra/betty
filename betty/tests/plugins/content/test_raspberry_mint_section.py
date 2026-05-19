from betty.content import ContentManufacturer
from betty.document import Document
from betty.locale.localizable.plain import Plain
from betty.plugins.content.raspberry_mint_section import Section, SectionData
from betty.plugins.content.render import Render, RenderData
from betty.plugins.content.static import Static
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestSectionData(DataTestBase[SectionData]):
    sut_cls = SectionData

    def test_content(self) -> None:
        sut = SectionData(ContentManufacturer("my-first-content"), heading="-")
        assert sut.content[0].plugin_id == "my-first-content"

    def test_heading(self) -> None:
        heading = Plain("My First Section")
        sut = SectionData(ContentManufacturer("my-first-content"), heading=heading)
        assert sut.heading is heading

    def test_name(self) -> None:
        sut = SectionData(
            ContentManufacturer("my-first-content"),
            name="my-first-section",
            heading="-",
        )
        assert sut.name == "my-first-section"

    def test_visually_hide_heading(self) -> None:
        sut = SectionData(
            ContentManufacturer("my-first-content"),
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
                SectionData(
                    ContentManufacturer(Static),
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
                SectionData(
                    ContentManufacturer(
                        Render,
                        RenderData("My First Content"),
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
                SectionData(
                    ContentManufacturer(
                        Render,
                        RenderData("My First Content"),
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
                SectionData(
                    ContentManufacturer(
                        Render,
                        RenderData("My First Content"),
                    ),
                    visually_hide_heading=True,
                    heading="My First Section",
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "visually-hidden" in actual
