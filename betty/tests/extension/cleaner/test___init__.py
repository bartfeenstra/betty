from __future__ import annotations

from betty.app import App
from betty.extension import Cleaner
from betty.load import load
from betty.model.ancestry import Event
from betty.model.event_type import Birth
from betty.project import ExtensionConfiguration


class TestCleaner:
    async def test_post_parse(self) -> None:
        event = Event('E0', Birth)

        app = App()
        app.project.configuration.extensions.append(ExtensionConfiguration(Cleaner))
        app.project.ancestry.entities.append(event)
        await load(app)

        assert [] == list(app.project.ancestry.entities[Event])
