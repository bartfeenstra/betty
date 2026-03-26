import pytest

from betty.app import App
from betty.document import Document
from betty.plugins.content.raspberry_mint_enclosees import Enclosees
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.project import Project


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
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Enclosees]) as project,
            project,
        ):
            sut = await Enclosees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_enclosee(self, isolated_app: App) -> None:
        enclosee = Place()
        resource = Place()
        Enclosure(enclosee, resource)
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Enclosees]) as project,
            project,
        ):
            sut = await Enclosees.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert enclosee.public_id in actual
