from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.document import Document
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.media_type import MediaType
from betty.plugins.content.raspberry_mint_media import Media
from betty.plugins.entity.file import File
from betty.test_utils.conftest import IsolatedProjectFactory


class TestMedia:
    async def test_build_template__without_file(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(support_plugins=[Media]) as project:
            sut = await Media.new(project)
            assert await sut.build(document=Document(object())) is None

    async def test_build_template__with_file(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        resource = File(
            ASSETS_DIRECTORY_PATH
            / "universe"
            / "public"
            / "static"
            / "betty-16x16.png",
            media_type=MediaType("image/png"),
        )
        async with isolated_project_factory(support_plugins=[Media]) as project:
            sut = await Media.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert resource.label.localize(DEFAULT_LOCALIZER) in actual
