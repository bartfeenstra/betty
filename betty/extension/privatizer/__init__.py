from __future__ import annotations

from collections import defaultdict

from betty.app.extension import UserFacingExtension
from betty.load import PostLoader, getLogger
from betty.locale import Localizer
from betty.model import Entity
from betty.model.ancestry import Person, HasMutablePrivacy
from betty.privatizer import Privatizer as PrivatizerApi


class _Privatizer(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        self.privatize()

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Privatizer')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Determine if people can be proven to have died. If not, mark them and their associated entities private.')

    def privatize(self) -> None:
        logger = getLogger()
        logger.info(self._app.localizer._('Privatizing...'))

        privatizer = PrivatizerApi(self._app.project.configuration.lifetime_threshold)

        newly_privatized: dict[type[HasMutablePrivacy & Entity], int] = defaultdict(lambda: 0)
        entities: list[HasMutablePrivacy & Entity] = []
        for entity in self._app.project.ancestry:
            if isinstance(entity, HasMutablePrivacy):
                entities.append(entity)
                if entity.private:
                    newly_privatized[
                        entity.type  # type: ignore[index]
                    ] -= 1

        for entity in entities:
            privatizer.privatize(entity)

        for entity in entities:
            if entity.private:
                newly_privatized[entity.type] += 1  # type: ignore[index]

        if newly_privatized[Person] > 0:
            logger.info(self._app.localizer._('Privatized {count} people because they are likely still alive.').format(
                count=newly_privatized[Person],
            ))
        for entity_type in set(newly_privatized) - {Person}:
            if newly_privatized[entity_type] > 0:
                logger.info(self._app.localizer._('Privatized {count} {entity_type}, because they are associated with private people.').format(
                    count=newly_privatized[entity_type],
                    entity_type=entity_type.entity_type_label_plural(self._app.localizer),
                ))
