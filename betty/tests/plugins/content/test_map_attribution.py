from betty.document import Document
from betty.plugins.content.map_attribution import MapAttribution
from betty.test_utils.conftest import IsolatedProjectFactory


class TestMapAttribution:
    async def test_build_template(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            support_plugins=[MapAttribution]
        ) as project:
            sut = await MapAttribution.new(project)
            actual = await sut.build(document=Document())
        assert actual
