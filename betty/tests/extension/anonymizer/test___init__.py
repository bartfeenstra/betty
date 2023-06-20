from __future__ import annotations

from betty.app import App
from betty.extension import Anonymizer
from betty.load import load
from betty.model.ancestry import Person, PersonName
from betty.project import ExtensionConfiguration


class TestAnonymizer:
    async def test_post_load(self) -> None:
        person = Person('P0')
        person.private = True
        PersonName(person, 'Jane', 'Dough')

        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(Anonymizer))
        app.project.ancestry.entities.append(person)
        await load(app)

        assert 0 == len(person.names)
