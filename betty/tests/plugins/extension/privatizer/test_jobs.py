from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.source import Source
from betty.plugins.event_type import Birth
from betty.plugins.extension.privatizer import Privatizer
from betty.plugins.role import Subject
from betty.privacy import Privacy
from betty.project import Project
from betty.project.load import load

if TYPE_CHECKING:
    from betty.app import App


class TestPrivatizeAncestry:
    async def test_do(self, isolated_app: App) -> None:
        person = Person(id="P0")
        Presence(person, Subject(), Event(event_type=Birth()))

        source_file = File(
            id="F0",
            path=Path(__file__),
        )
        source = Source(
            id="S0",
            name="The Source",
            privacy=Privacy.PRIVATE,
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
            privacy=Privacy.PRIVATE,
        )
        FileReference(citation, citation_file)

        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Privatizer)
            project.ancestry.add(person, source, citation)
            async with project:
                await load(project)

            assert person.private
            assert source_file.private
            assert citation_file.private
