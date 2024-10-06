"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import final

from typing_extensions import override

from betty.project.extension.gramps.config import GrampsConfiguration
from betty.gramps.loader import GrampsLoader
from betty.locale.localizable import static, _
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension
from betty.project.load import LoadAncestryEvent

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry


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
                factory=project.new_target,
                localizer=await project.app.localizer,
                copyright_notices=project.copyright_notices,
                licenses=await project.licenses,
                event_type_map=await family_tree_configuration.event_types.to_plugins(
                    project.event_types
                ),
                gender_map=await family_tree_configuration.genders.to_plugins(
                    project.genders
                ),
                place_type_map=await family_tree_configuration.place_types.to_plugins(
                    project.place_types
                ),
                presence_role_map=await family_tree_configuration.presence_roles.to_plugins(
                    project.presence_roles
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
    def default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(LoadAncestryEvent, _load_ancestry)
