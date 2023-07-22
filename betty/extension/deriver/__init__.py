from __future__ import annotations

import logging

from betty.app.extension import Extension, UserFacingExtension
from betty.deriver import Deriver
from betty.load import PostLoader
from betty.locale import Localizer
from betty.model.ancestry import Person, Ancestry
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType


class _Deriver(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        await self.derive(self.app.project.ancestry)

    async def derive(self, ancestry: Ancestry) -> None:
        logger = logging.getLogger()
        deriver = Deriver(self.app.event_types)
        for event_type in self.app.event_types:
            if issubclass(event_type, DerivableEventType):
                created_derivations = 0
                updated_derivations = 0
                for person in ancestry[Person]:
                    created, updated = deriver.derive_person(person, event_type)
                    created_derivations += created
                    updated_derivations += updated
                logger.info(self.app.localizer._('Updated {updated_derivations} {event_type} events based on existing information.').format(
                    updated_derivations=updated_derivations,
                    event_type=event_type.label(self.app.localizer)),
                )
                if issubclass(event_type, CreatableDerivableEventType):
                    logger.info(self.app.localizer._('Created {created_derivations} additional {event_type} events based on existing information.').format(
                        created_derivations=created_derivations,
                        event_type=event_type.label(self.app.localizer)),
                    )

    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
        from betty.extension import Privatizer

        return {Privatizer}

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Deriver')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Create events such as births and deaths by deriving their details from existing information.')
