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
from betty.locale.localizable import static, _, Localizable
from betty.project.extension import ConfigurableExtension

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.machine_name import MachineName


async def _load_ancestry(event: LoadAncestryEvent) -> None:
    project = event.project
    gramps_configuration = project.configuration.extensions[
        Gramps
    ].extension_configuration
    assert isinstance(gramps_configuration, GrampsConfiguration)
    for family_tree_configuration in gramps_configuration.family_trees:
        file_path = family_tree_configuration.file_path
        if file_path:
            await GrampsLoader(
                project.ancestry,
                attribute_prefix_key=project.configuration.name,
                factory=project.new,
                localizer=project.app.localizer,
                event_type_map=await family_tree_configuration.event_types.to_plugins(
                    project.event_types
                ),
                place_type_map=await family_tree_configuration.place_types.to_plugins(
                    project.place_types
                ),
                presence_role_map=await family_tree_configuration.presence_roles.to_plugins(
                    project.presence_roles
                ),
            ).load_file(file_path)


@final
class Gramps(ConfigurableExtension[GrampsConfiguration]):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
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
        return static("Gramps")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')
