import pytest

from betty.document import Document
from betty.plugins.content.raspberry_mint_enclosees import Enclosees
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.test_utils.conftest import IsolatedProjectFactory


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
        self, resource: object, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Enclosees]) as project:
            sut = await Enclosees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_enclosee(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        enclosee = Place()
        resource = Place()
        Enclosure(enclosee, resource)
        async with isolated_project_factory(supported_plugins=[Enclosees]) as project:
            sut = await Enclosees.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert enclosee.public_id in actual
