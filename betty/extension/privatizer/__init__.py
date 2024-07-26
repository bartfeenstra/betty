"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.load import PostLoadAncestryEvent
from betty.locale.localizable import _, Localizable
from betty.model.ancestry import Person, HasPrivacy
from betty.privatizer import Privatizer as PrivatizerApi
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.machine_id import MachineId
    from betty.model import Entity


async def _privatize_ancestry(event: PostLoadAncestryEvent) -> None:
    logger = getLogger(__name__)
    logger.info(event.project.app.localizer._("Privatizing..."))

    privatizer = PrivatizerApi(
        event.project.configuration.lifetime_threshold,
        localizer=event.project.app.localizer,
    )

    newly_privatized: dict[type[HasPrivacy & Entity], int] = defaultdict(lambda: 0)
    entities: list[HasPrivacy & Entity] = []
    for entity in event.project.ancestry:
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
            event.project.app.localizer._(
                "Privatized {count} people because they are likely still alive."
            ).format(
                count=str(newly_privatized[Person]),
            )
        )
    for entity_type in set(newly_privatized) - {Person}:
        if newly_privatized[entity_type] > 0:
            logger.info(
                event.project.app.localizer._(
                    "Privatized {count} {entity_type}, because they are associated with private information."
                ).format(
                    count=str(newly_privatized[entity_type]),
                    entity_type=entity_type.plugin_label_plural().localize(
                        event.project.app.localizer
                    ),
                )
            )


@final
class Privatizer(Extension):
    """
    Extend the Betty Application with privatization features.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineId:
        return "privatizer"

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _privatize_ancestry)

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Privatizer")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            "Determine if people can be proven to have died. If not, mark them and their associated entities private."
        )
