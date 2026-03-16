from pathlib import Path

import pytest

from betty.app import App
from betty.document import Document
from betty.plugins.content.raspberry_mint_file_referees import FileReferees
from betty.plugins.entity.file import File
from betty.plugins.entity.file_reference import FileReference
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences


class TestFileReferees:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            File(Path(__file__)),
        ],
    )
    async def test_build_template__without_referees(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await FileReferees.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_referee(self, isolated_app: App) -> None:
        referee = DummyHasFileReferences()
        resource = File(Path(__file__))
        FileReference(referee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await FileReferees.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert referee.public_id in actual
