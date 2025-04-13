"""Privatize people and associated data by determining if they are likely to be alive."""

from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.person import Person
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy
from betty.privacy.privatizer import Privatizer as PrivatizerApi
from betty.project.extension import Extension
from betty.project.load import PostLoadAncestryEvent

if TYPE_CHECKING:
    from collections.abc import MutableMapping, MutableSequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.model import Entity


async def _privatize_ancestry(event: PostLoadAncestryEvent) -> None:
    localizer = await event.project.app.localizer
    logger = getLogger(__name__)
    logger.info(localizer._("Privatizing..."))

    privatizer = PrivatizerApi(
        event.project.configuration.lifetime_threshold,
        localizer=localizer,
    )

    newly_privatized: MutableMapping[type[HasPrivacy & Entity], int] = defaultdict(
        lambda: 0
    )
    entities: MutableSequence[HasPrivacy & Entity] = []
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
            localizer._(
                "Privatized {count} people because they are likely still alive."
            ).format(
                count=str(newly_privatized[Person]),
            )
        )
    for entity_type in set(newly_privatized) - {Person}:
        if newly_privatized[entity_type] > 0:
            logger.info(
                localizer._(
                    "Privatized {count} {entity_type}, because they are associated with private information."
                ).format(
                    count=str(newly_privatized[entity_type]),
                    entity_type=entity_type.plugin_label_plural().localize(localizer),
                )
            )


@final
class Privatizer(ShorthandPluginBase, Extension):
    """
    Extend the Betty Application with privatization features.
    """

    _plugin_id = "privatizer"
    _plugin_label = _("Privatizer")
    _plugin_description = _(
        "Determine if people can be proven to have died. If not, mark them and their associated entities private."
    )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _privatize_ancestry)
