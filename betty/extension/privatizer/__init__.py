from __future__ import annotations

import logging

from betty.app.extension import UserFacingExtension
from betty.load import PostLoader
from betty.locale import Localizer
from betty.model.ancestry import Person, Event, Citation, Source, File
from betty.privatizer import Privatizer as PrivatizerApi


class _Privatizer(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        self.privatize()

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Privatizer')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Determine if people can be proven to have died. If not, mark them and their related resources private, but only if they are not already explicitly marked public or private. Enable the Anonymizer and Cleaner as well to make this most effective.')

    def privatize(self) -> None:
        privatizer = PrivatizerApi(self._app.project.configuration.lifetime_threshold)

        privatized = 0
        for person in self._app.project.ancestry.entities[Person]:
            private = person.private
            privatizer.privatize(person)
            if private is None and person.private is True:
                privatized += 1
        logger = logging.getLogger()
        logger.info(self._app.localizer._('Privatized {count} people because they are likely still alive.').format(count=privatized))

        for citation in self._app.project.ancestry.entities[Citation]:
            privatizer.privatize(citation)

        for source in self._app.project.ancestry.entities[Source]:
            privatizer.privatize(source)

        for event in self._app.project.ancestry.entities[Event]:
            privatizer.privatize(event)

        for file in self._app.project.ancestry.entities[File]:
            privatizer.privatize(file)
