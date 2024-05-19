from __future__ import annotations

from pathlib import Path

from betty.app import App
from betty.extension import Privatizer
from betty.load import load
from betty.model.ancestry import (
    Person,
    Presence,
    Event,
    Source,
    File,
    Subject,
    Citation,
)
from betty.model.event_type import Birth
from betty.project import ExtensionConfiguration


class TestPrivatizer:
    async def test_post_load(self, new_temporary_app: App) -> None:
        person = Person(id="P0")
        Presence(person, Subject(), Event(event_type=Birth))

        source_file = File(
            id="F0",
            path=Path(__file__),
        )
        source = Source(
            id="S0",
            name="The Source",
            private=True,
        )
        source.files.add(source_file)

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
        citation.files.add(citation_file)

        new_temporary_app.project.configuration.extensions.append(
            ExtensionConfiguration(Privatizer)
        )
        new_temporary_app.project.ancestry.add(person, source, citation)
        await load(new_temporary_app)

        assert person.private
        assert source_file.private
        assert citation_file.private
