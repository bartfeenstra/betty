from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from betty.load import load
from betty.plugins.enricher.privatizer import Privatizer
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.event import Event
from betty.plugins.entity.file import File
from betty.plugins.entity.file_reference import FileReference
from betty.plugins.entity.person import Person
from betty.plugins.entity.presence import Presence
from betty.plugins.entity.source import Source
from betty.plugins.event_type.birth import Birth
from betty.plugins.role.subject import Subject
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestPrivatizeAncestry:
    async def test_do(self, isolated_project_factory: IsolatedProjectFactory) -> None:
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

        async with isolated_project_factory(enrichers=[Privatizer]) as project:
            project.ancestry.add(person, source, citation)
            await load(project)

        assert person.private
        assert source_file.private
        assert citation_file.private
