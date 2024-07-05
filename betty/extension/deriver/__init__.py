"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from logging import getLogger

from typing_extensions import override

from betty.deriver import Deriver as DeriverApi
from betty.load import PostLoader
from betty.locale.localizable import _, Localizable
from betty.model.event_type import DerivableEventType
from betty.project.extension import Extension, UserFacingExtension


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
        logger.info(self._project.app.localizer._("Deriving..."))

        deriver = DeriverApi(
            self.project.ancestry,
            self.project.configuration.lifetime_threshold,
            {
                event_type
                for event_type in self.project.event_types
                if issubclass(event_type, DerivableEventType)
            },
            localizer=self.project.app.localizer,
        )
        await deriver.derive()

    @override
    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
        from betty.extension import Privatizer

        return {Privatizer}

    @override
    @classmethod
    def label(cls) -> Localizable:
        return _("Deriver")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return _(
            "Create events such as births and deaths by deriving their details from existing information."
        )
