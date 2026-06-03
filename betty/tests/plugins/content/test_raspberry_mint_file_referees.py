import pytest

from betty.document import Document
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.person import Person
from betty.entities.place import Place
from betty.plugins.content.raspberry_mint_file_referees import FileReferees
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.conftest import IsolatedProjectFactory


class TestFileReferees:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            File(__file__),
        ],
    )
    async def test_build_template__without_referees(
        self, resource: object, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            supported_plugins=[FileReferees]
        ) as project:
            sut = await FileReferees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_referee(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        referee = DummyHasFileReferences()
        resource = File(__file__)
        FileReference(referee, resource)
        async with isolated_project_factory(
            supported_plugins=[FileReferees]
        ) as project:
            sut = await FileReferees.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert referee.public_id in actual
