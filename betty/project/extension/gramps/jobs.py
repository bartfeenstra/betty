"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from typing_extensions import override

from betty.ancestry.event_type import EventTypePlugin
from betty.ancestry.gender import GenderPlugin
from betty.ancestry.place_type import PlaceTypePlugin
from betty.ancestry.presence_role import PresenceRolePlugin
from betty.copyright_notice import CopyrightNoticePlugin
from betty.gramps.loader import GrampsLoader
from betty.job import Job
from betty.license import LicensePlugin
from betty.plugin import Plugin, PluginDefinition
from betty.project import ProjectContext

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.job.scheduler import Scheduler
    from betty.plugin.config import PluginInstanceConfiguration
    from betty.plugin.repository import PluginRepository
    from betty.project.factory import ProjectFactory

_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


def _new_plugin_instance_factory(
    configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    repository: PluginRepository[_PluginDefinitionT],
    *,
    factory: ProjectFactory,
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
                copyright_notices=await project.plugins(CopyrightNoticePlugin),
                licenses=await project.plugins(LicensePlugin),
                event_type_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.event_types[gramps_type],
                        await project.plugins(EventTypePlugin),
                        factory=project.new_target,
                    )
                    for gramps_type in family_tree_configuration.event_types
                },
                genders=await project.plugins(GenderPlugin),
                place_type_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.place_types[gramps_type],
                        await project.plugins(PlaceTypePlugin),
                        factory=project.new_target,
                    )
                    for gramps_type in family_tree_configuration.place_types
                },
                presence_role_mapping={
                    gramps_type: _new_plugin_instance_factory(
                        family_tree_configuration.presence_roles[gramps_type],
                        await project.plugins(PresenceRolePlugin),
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
