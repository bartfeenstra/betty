from __future__ import annotations

from pathlib import Path

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
from betty.project import ExtensionConfiguration, Project
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.app import App


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

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Privatizer))
            project.ancestry.add(person, source, citation)
            async with project:
                await load(project)

            assert person.private
            assert source_file.private
            assert citation_file.private
