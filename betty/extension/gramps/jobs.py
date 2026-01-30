"""
Jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypeVar, override

from betty.gramps.loader import GrampsLoader
from betty.job import Job
from betty.plugin import Plugin, PluginDefinition
from betty.project.job import ProjectContext

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler

_T = TypeVar("_T")
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class LoadAncestry(Job[ProjectContext]):
    """
    Load Gramps data into an ancestry.
    """

    def __init__(self):
        super().__init__("gramps:load-ancestry")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        from betty.extension.gramps import Gramps

        project = scheduler.context.project
        extensions = await project.extensions
        gramps_configuration = extensions[Gramps].configuration
        for family_tree_configuration in gramps_configuration.family_trees:
            source = family_tree_configuration.source

            loader = GrampsLoader(
                project.ancestry,
                services=project,
                attribute_prefix_key=project.configuration.name,
                user=project.app.user,
                event_type_mapping=family_tree_configuration.event_types,
                place_type_mapping=family_tree_configuration.place_types,
                presence_role_mapping=family_tree_configuration.presence_roles,
                executable=gramps_configuration.executable,
            )
            if isinstance(source, str):
                await loader.load_name(source)
            else:
                await loader.load_file(source)
