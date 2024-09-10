from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typing_extensions import override

from betty.extension.privatizer import Privatizer
from betty.load import load
from betty.ancestry import (
    Person,
    Presence,
    Event,
    Source,
    File,
    Citation,
    FileReference,
)
from betty.ancestry.event_type import Birth
from betty.ancestry.presence_role import Subject
from betty.project import Project
from betty.project.config import ExtensionConfiguration
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App


class TestPrivatizer(ExtensionTestBase):
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
            project.configuration.extensions.append(ExtensionConfiguration(Privatizer))
            project.ancestry.add(person, source, citation)
            async with project:
                await load(project)

            assert person.private
            assert source_file.private
            assert citation_file.private
