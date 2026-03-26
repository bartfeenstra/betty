from betty.app import App
from betty.document import Document
from betty.plugins.content.map_attribution import MapAttribution
from betty.project import Project


class TestMapAttribution:
    async def test_build_template(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(
                isolated_app, support_plugins=[MapAttribution]
            ) as project,
            project,
        ):
            sut = await MapAttribution.new(project)
            actual = await sut.build(document=Document())
        assert actual
