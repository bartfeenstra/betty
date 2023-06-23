from __future__ import annotations

from betty.app.extension import Extension, UserFacingExtension
from betty.deriver import Deriver
from betty.load import PostLoader, getLogger
from betty.locale import Localizer
from betty.model.event_type import DerivableEventType


class _Deriver(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        logger = getLogger()
        logger.info(self._app.localizer._('Deriving...'))

        deriver = Deriver(
            self.app.project.ancestry,
            self.app.project.configuration.lifetime_threshold,
            {
                event_type
                for event_type
                in self.app.event_types
                if issubclass(event_type, DerivableEventType)
            },
            localizer=self.app.localizer,
        )
        await deriver.derive()

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
