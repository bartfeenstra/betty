"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from logging import getLogger

from typing_extensions import override

from betty.app.extension import Extension, UserFacingExtension
from betty.deriver import Deriver as DeriverApi
from betty.load import PostLoader
from betty.locale import Str
from betty.model.event_type import DerivableEventType


class Deriver(UserFacingExtension, PostLoader):
    """
    Expand an ancestry by deriving additional data from existing data.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Deriver"

    @override
    async def post_load(self) -> None:
        logger = getLogger(__name__)
        logger.info(self._app.localizer._("Deriving..."))

        deriver = DeriverApi(
            self.app.project.ancestry,
            self.app.project.configuration.lifetime_threshold,
            {
                event_type
                for event_type in self.app.event_types
                if issubclass(event_type, DerivableEventType)
            },
            localizer=self._app.localizer,
        )
        await deriver.derive()

    @override
    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
        from betty.extension import Privatizer

        return {Privatizer}

    @override
    @classmethod
    def label(cls) -> Str:
        return Str._("Deriver")

    @override
    @classmethod
    def description(cls) -> Str:
        return Str._(
            "Create events such as births and deaths by deriving their details from existing information."
        )
