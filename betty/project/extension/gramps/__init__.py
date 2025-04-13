"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, final

from typing_extensions import override

from betty.gramps.loader import GrampsLoader
from betty.locale.localizable import _, static
from betty.plugin import Plugin, PluginRepository, ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.load import LoadAncestryEvent

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin.config import PluginInstanceConfiguration

_PluginT = TypeVar("_PluginT", bound=Plugin)


def _new_plugin_instance_factory(
    configuration: PluginInstanceConfiguration, repository: PluginRepository[_PluginT]
) -> Callable[[], Awaitable[_PluginT]]:
    async def plugin_instance_factory() -> _PluginT:
        return await configuration.new_plugin_instance(repository)

    return plugin_instance_factory


async def _load_ancestry(event: LoadAncestryEvent) -> None:
    project = event.project
    extensions = await project.extensions
    gramps_configuration = extensions[Gramps].configuration
    for family_tree_configuration in gramps_configuration.family_trees:
        file_path = family_tree_configuration.file_path
        if not file_path:
            continue

        await GrampsLoader(
            project.ancestry,
            attribute_prefix_key=project.configuration.name,
            localizer=await project.app.localizer,
            copyright_notices=project.copyright_notice_repository,
            licenses=await project.license_repository,
            event_type_mapping={
                gramps_type: _new_plugin_instance_factory(
                    family_tree_configuration.event_types[gramps_type],
                    project.event_type_repository,
                )
                for gramps_type in family_tree_configuration.event_types
            },
            genders=project.gender_repository,
            place_type_mapping={
                gramps_type: _new_plugin_instance_factory(
                    family_tree_configuration.place_types[gramps_type],
                    project.place_type_repository,
                )
                for gramps_type in family_tree_configuration.place_types
            },
            presence_role_mapping={
                gramps_type: _new_plugin_instance_factory(
                    family_tree_configuration.presence_roles[gramps_type],
                    project.presence_role_repository,
                )
                for gramps_type in family_tree_configuration.presence_roles
            },
        ).load_file(file_path)


@final
class Gramps(ShorthandPluginBase, ConfigurableExtension[GrampsConfiguration]):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    _plugin_id = "gramps"
    _plugin_label = static("Gramps")
    _plugin_description = _(
        'Load <a href="https://gramps-project.org/">Gramps</a> family trees.'
    )

    @override
    @classmethod
    def new_default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(LoadAncestryEvent, _load_ancestry)
