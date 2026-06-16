from __future__ import annotations

from typing import TYPE_CHECKING

from betty.enrichers.privatizer import Privatizer
from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.event_types.birth import Birth
from betty.load import load
from betty.privacy import Privacy
from betty.roles.subject import Subject

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestPrivatizeAncestry:
    async def test_do(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        person = Person(id="my-first-person")
        Presence(person, Subject(), Event(event_type=Birth()))

        source_file = File(id="my-first-file", path=__file__)
        source = Source(
            id="my-first-source",
            name="The Source",
            privacy=Privacy.PRIVATE,
        )
        FileReference(source, source_file)

        citation_file = File(id="my-first-file", path=__file__)
        citation_source = Source("The Source")
        citation = Citation(
            id="my-first-citation",
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
