"""
Expand an ancestry by deriving additional data from existing data.
"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry import event_type
from betty.ancestry.event_type.event_types import DerivableEventType
from betty.deriver import Deriver as DeriverApi
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import Extension
from betty.project.extension.privatizer import Privatizer
from betty.project.load import PostLoadAncestryEvent

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier


async def _derive_ancestry(event: PostLoadAncestryEvent) -> None:
    project = event.project
    localizer = await project.app.localizer
    logger = getLogger(__name__)
    logger.info(localizer._("Deriving..."))

    deriver = DeriverApi(
        project.ancestry,
        project.configuration.lifetime_threshold,
        project.event_type_repository,
        set(
            await event_type.EVENT_TYPE_REPOSITORY.select(
                DerivableEventType  # type: ignore[type-abstract]
            )
        ),
        localizer=localizer,
    )
    await deriver.derive()


@final
class Deriver(ShorthandPluginBase, Extension):
    """
    Expand an ancestry by deriving additional data from existing data.
    """

    _plugin_id = "deriver"
    _plugin_label = _("Deriver")
    _plugin_description = _(
        "Create events such as births and deaths by deriving their details from existing information."
    )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(PostLoadAncestryEvent, _derive_ancestry)

    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
        return {Privatizer}
