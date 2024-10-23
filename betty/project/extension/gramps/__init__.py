"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import final

from typing_extensions import override

from betty.gramps.loader import GrampsLoader
from betty.locale.localizable import static, _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.extension.gramps.config import GrampsConfiguration
from betty.project.load import LoadAncestryEvent

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry


async def _load_ancestry(event: LoadAncestryEvent) -> None:
    project = event.project
    extensions = await project.extensions
    gramps_configuration = extensions[Gramps].configuration
    for family_tree_configuration in gramps_configuration.family_trees:
        file_path = family_tree_configuration.file_path
        if file_path:
            await GrampsLoader(
                project.ancestry,
                attribute_prefix_key=project.configuration.name,
                factory=project.new_target,
                localizer=await project.app.localizer,
                copyright_notices=project.copyright_notice_repository,
                licenses=await project.license_repository,
                event_type_map=await family_tree_configuration.event_types.to_plugins(
                    project.event_type_repository
                ),
                gender_map=await family_tree_configuration.genders.to_plugins(
                    project.gender_repository
                ),
                place_type_map=await family_tree_configuration.place_types.to_plugins(
                    project.place_type_repository
                ),
                presence_role_map=await family_tree_configuration.presence_roles.to_plugins(
                    project.presence_role_repository
                ),
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
