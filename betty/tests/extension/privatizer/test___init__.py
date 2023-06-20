from __future__ import annotations

from pathlib import Path

from betty.app import App
from betty.extension import Privatizer
from betty.load import load
from betty.model.ancestry import Person, Presence, Event, Source, File, Subject, Citation
from betty.model.event_type import Birth
from betty.project import ExtensionConfiguration


class TestPrivatizer:
    async def test_post_load(self) -> None:
        person = Person('P0')
        Presence(person, Subject(), Event(None, Birth))

        source_file = File('F0', Path(__file__))
        source = Source('S0', 'The Source')
        source.private = True
        source.files.append(source_file)

        citation_file = File('F0', Path(__file__))
        citation_source = Source('The Source')
        citation = Citation('C0', citation_source)
        citation.private = True
        citation.files.append(citation_file)

        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(Privatizer))
        app.project.ancestry.entities.append(person, source, citation)
        await load(app)

        assert person.private
        assert source_file.private
        assert citation_file.private
