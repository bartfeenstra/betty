"""Privatize people and associated data by determining if they are likely to be alive."""
from __future__ import annotations

from collections import defaultdict
from logging import getLogger

from betty.app.extension import UserFacingExtension
from betty.load import PostLoader
from betty.locale import Str
from betty.model import Entity
from betty.model.ancestry import Person, HasPrivacy
from betty.privatizer import Privatizer as PrivatizerApi


class _Privatizer(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        self.privatize()

    @classmethod
    def label(cls) -> Str:
        return Str._('Privatizer')

    @classmethod
    def description(cls) -> Str:
        return Str._('Determine if people can be proven to have died. If not, mark them and their associated entities private.')

    def privatize(self) -> None:
        logger = getLogger(__name__)
        logger.info(self._app.localizer._('Privatizing...'))

        privatizer = PrivatizerApi(
            self._app.project.configuration.lifetime_threshold,
            localizer=self._app.localizer,
        )

        newly_privatized: dict[type[HasPrivacy & Entity], int] = defaultdict(lambda: 0)
        entities: list[HasPrivacy & Entity] = []
        for entity in self._app.project.ancestry:
            if isinstance(entity, HasPrivacy):
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
                count=str(newly_privatized[Person]),
            ))
        for entity_type in set(newly_privatized) - {Person}:
            if newly_privatized[entity_type] > 0:
                logger.info(self._app.localizer._('Privatized {count} {entity_type}, because they are associated with private information.').format(
                    count=str(newly_privatized[entity_type]),
                    entity_type=entity_type.entity_type_label_plural().localize(self._app.localizer),
                ))
