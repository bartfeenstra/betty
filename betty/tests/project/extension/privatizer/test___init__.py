from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.project import Project
from betty.project.extension.privatizer import Privatizer
from betty.project.load import load
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App


class TestPrivatizer(ExtensionTestBase[Privatizer]):
    @override
    def get_sut_class(self) -> type[Privatizer]:
        return Privatizer

    async def test_post_load(self, new_temporary_app: App) -> None:
        person = Person(id="P0")
        Presence(person, Subject(), Event(event_type=Birth()))

        source_file = File(
            id="F0",
            path=Path(__file__),
        )
        source = Source(
            id="S0",
            name="The Source",
            private=True,
        )
        FileReference(source, source_file)

        citation_file = File(
            id="F0",
            path=Path(__file__),
        )
        citation_source = Source("The Source")
        citation = Citation(
            id="C0",
            source=citation_source,
            private=True,
        )
        FileReference(citation, citation_file)

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Privatizer)
            project.ancestry.add(person, source, citation)
            async with project:
                await load(project)

            assert person.private
            assert source_file.private
            assert citation_file.private
