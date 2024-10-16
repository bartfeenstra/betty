"""
Provide demonstration site functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import static
from betty.plugin import ShorthandPluginBase
from betty.project.extension import Extension
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.extension.demo.project import load_ancestry
from betty.project.extension.deriver import Deriver
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.trees import Trees
from betty.project.extension.wikipedia import Wikipedia
from betty.project.load import LoadAncestryEvent

if TYPE_CHECKING:
    from betty.plugin import PluginIdentifier
    from betty.event_dispatcher import EventHandlerRegistry


@final
class Demo(ShorthandPluginBase, Extension):
    """
    Provide demonstration site functionality.
    """

    _plugin_id = "demo"
    _plugin_label = static("Demo")

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {
            CottonCandy,
            Deriver,
            HttpApiDoc,
            Maps,
            Trees,
            Wikipedia,
        }

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(
            LoadAncestryEvent, lambda event: load_ancestry(event.project)
        )
