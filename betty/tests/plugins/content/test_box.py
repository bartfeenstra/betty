from betty.content import ContentManufacturer
from betty.document import Document
from betty.plugins.content.box import Box, BoxConfiguration
from betty.plugins.content.render import Render, RenderConfiguration
from betty.project import Project
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestBoxConfiguration(DataTestBase[BoxConfiguration]):
    sut_cls = BoxConfiguration

    def test_content(self) -> None:
        sut = BoxConfiguration("my-first-content")
        assert sut.content[0].plugin_id == "my-first-content"


class TestBox:
    async def test_build_template__minimal(self, isolated_project: Project) -> None:
        sut = await Box.new(
            isolated_project,
            BoxConfiguration(
                ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))
            ),
        )
        actual = await sut.build(document=Document())
        assert actual is not None
        assert "<div>" in actual

    async def test_build_template__full(self, isolated_project: Project) -> None:
        sut = await Box.new(
            isolated_project,
            BoxConfiguration(
                ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE)),
                min_height="MIN_HEIGHT",
                max_height="MAX_HEIGHT",
                height="HEIGHT",
                min_width="MIN_WIDTH",
                max_width="MAX_WIDTH",
                width="WIDTH",
            ),
        )
        actual = await sut.build(document=Document())
        assert actual is not None
        assert "<div>" not in actual
        assert "min-height: MIN_HEIGHT;" in actual
        assert "max-height: MAX_HEIGHT;" in actual
        assert "height: HEIGHT;" in actual
        assert "min-width: MIN_WIDTH;" in actual
        assert "max-width: MAX_WIDTH;" in actual
        assert "width: WIDTH;" in actual
