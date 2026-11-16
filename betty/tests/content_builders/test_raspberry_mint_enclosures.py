import pytest

from betty.content_builders.raspberry_mint_enclosures import Enclosures
from betty.document import Document
from betty.entities.enclosure import Enclosure
from betty.entities.person import Person
from betty.entities.place import Place
from betty.test_utils.conftest import NewIsolatedProject


class TestEnclosures:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_enclosures(
        self, resource: object, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Enclosures]) as project,
            project,
        ):
            sut = await Enclosures.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_enclosures(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        encloses = Place()
        resource = Place()
        Enclosure(encloses=encloses, enclosed_by=resource)
        async with (
            new_isolated_project(supported_plugins=[Enclosures]) as project,
            project,
        ):
            sut = await Enclosures.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert encloses.id in actual
