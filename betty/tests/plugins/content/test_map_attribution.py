from betty.app import App
from betty.document import Document
from betty.plugins.content.map_attribution import MapAttribution
from betty.plugins.extension.maps import Maps
from betty.project import Project


class TestMapAttribution:
    async def test_build_template(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                sut = await MapAttribution.new(project)
                actual = await sut.build(document=Document())
        assert actual
