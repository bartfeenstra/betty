"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from collections import defaultdict
from logging import getLogger

from typing_extensions import override

from betty.project.extension import UserFacingExtension
from betty.load import PostLoader
from betty.locale import Str, Localizable
from betty.model.ancestry import Person, HasPrivacy
from betty.privatizer import Privatizer as PrivatizerApi
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.model import Entity


class Privatizer(UserFacingExtension, PostLoader):
    """
    Extend the Betty Application with privatization features.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Privatizer"

    @override
    async def post_load(self) -> None:
        self.privatize()

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str._("Privatizer")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._(
            "Determine if people can be proven to have died. If not, mark them and their associated entities private."
        )

    def privatize(self) -> None:
        """
        Privatize the project's ancestry.
        """
        logger = getLogger(__name__)
        logger.info(self.project.app.localizer._("Privatizing..."))

        privatizer = PrivatizerApi(
            self.project.configuration.lifetime_threshold,
            localizer=self.project.app.localizer,
        )

        newly_privatized: dict[type[HasPrivacy & Entity], int] = defaultdict(lambda: 0)
        entities: list[HasPrivacy & Entity] = []
        for entity in self.project.ancestry:
            if isinstance(entity, HasPrivacy):
                entities.append(entity)
                if entity.private:
                    newly_privatized[entity.type] -= 1  # type: ignore[index]

        for entity in entities:
            privatizer.privatize(entity)

        for entity in entities:
            if entity.private:
                newly_privatized[entity.type] += 1  # type: ignore[index]

        if newly_privatized[Person] > 0:
            logger.info(
                self.project.app.localizer._(
                    "Privatized {count} people because they are likely still alive."
                ).format(
                    count=str(newly_privatized[Person]),
                )
            )
        for entity_type in set(newly_privatized) - {Person}:
            if newly_privatized[entity_type] > 0:
                logger.info(
                    self.project.app.localizer._(
                        "Privatized {count} {entity_type}, because they are associated with private information."
                    ).format(
                        count=str(newly_privatized[entity_type]),
                        entity_type=entity_type.entity_type_label_plural().localize(
                            self.project.app.localizer
                        ),
                    )
                )
