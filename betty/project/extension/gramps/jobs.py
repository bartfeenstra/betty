"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.gender import GenderDefinition
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.gramps.loader import GrampsLoader
from betty.job import Job
from betty.license import LicenseDefinition
from betty.project import ProjectContext

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.factory import Factory
    from betty.job.scheduler import Scheduler
    from betty.plugin import ClassedPluginDefinition, PluginRepository
    from betty.plugin.config import PluginInstanceConfiguration

_PluginT = TypeVar("_PluginT")


def _new_plugin_instance_factory(
    configuration: PluginInstanceConfiguration[
        ClassedPluginDefinition[_PluginT], _PluginT
    ],
    repository: PluginRepository[ClassedPluginDefinition[_PluginT]],
    *,
    factory: Factory,
) -> Callable[[], Awaitable[_PluginT]]:
    async def plugin_instance_factory() -> _PluginT:
        return await configuration.new_plugin_instance(repository, factory=factory)

    return plugin_instance_factory


class LoadAncestry(Job[ProjectContext]):
    """
    Load Gramps data into an ancestry.
    """

    def __init__(self):
        super().__init__("gramps:load-ancestry")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        from betty.project.extension.gramps import Gramps

        project = scheduler.context.project
        extensions = await project.extensions
        gramps_configuration = extensions[Gramps].configuration
        for family_tree_configuration in gramps_configuration.family_trees:
            source = family_tree_configuration.source

            loader = GrampsLoader(
                project.ancestry,
                factory=project.new_target,
                attribute_prefix_key=project.configuration.name,
                user=project.app.user,
                copyright_notices=await project.plugins(CopyrightNoticeDefinition),
                licenses=await project.plugins(LicenseDefinition),
                event_type_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.event_types[gramps_type],
                        await project.plugins(EventTypeDefinition),
                        factory=project.new_target,
                    )
                    for gramps_type in family_tree_configuration.event_types
                },
                genders=await project.plugins(GenderDefinition),
                place_type_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.place_types[gramps_type],
                        await project.plugins(PlaceTypeDefinition),
                        factory=project.new_target,
                    )
                    for gramps_type in family_tree_configuration.place_types
                },
                presence_role_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.presence_roles[gramps_type],
                        await project.plugins(PresenceRoleDefinition),
                        factory=project.new_target,
                    )
                    for gramps_type in family_tree_configuration.presence_roles
                },
                executable=gramps_configuration.executable,
            )
            if isinstance(source, str):
                await loader.load_name(source)
            else:
                await loader.load_file(source)
