"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import final

from typing_extensions import override

from betty.extension.gramps.config import GrampsConfiguration
from betty.gramps.loader import GrampsLoader
from betty.load import LoadAncestryEvent
from betty.locale.localizable import plain, _, Localizable
from betty.project.extension import ConfigurableExtension

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginId


async def _load_ancestry(event: LoadAncestryEvent) -> None:
    gramps_configuration = event.project.configuration.extensions[
        Gramps
    ].extension_configuration
    assert isinstance(gramps_configuration, GrampsConfiguration)
    for family_tree in gramps_configuration.family_trees:
        file_path = family_tree.file_path
        if file_path:
            await GrampsLoader(
                event.project,
                localizer=event.project.app.localizer,
            ).load_file(file_path)


@final
class Gramps(ConfigurableExtension[GrampsConfiguration]):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return "gramps"

    @override
    @classmethod
    def default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(LoadAncestryEvent, _load_ancestry)

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("Gramps")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')
