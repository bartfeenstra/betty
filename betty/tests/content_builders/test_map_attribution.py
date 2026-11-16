from betty.content_builders.map_attribution import MapAttribution
from betty.document import Document
from betty.test_utils.conftest import NewIsolatedProject


class TestMapAttribution:
    async def test_build_template(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[MapAttribution]) as project,
            project,
        ):
            sut = await MapAttribution.new(project)
            actual = await sut.build(document=Document())
        assert actual
