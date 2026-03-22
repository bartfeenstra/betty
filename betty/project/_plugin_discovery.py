from __future__ import annotations

from typing import TYPE_CHECKING

from betty.project import Project
from betty.requirement import require

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.copyright_notice import CopyrightNoticeDefinition
    from betty.event_type import EventTypeDefinition
    from betty.gender import GenderDefinition
    from betty.license import LicenseDefinition
    from betty.place_type import PlaceTypeDefinition
    from betty.plugin import PluginDefinition
    from betty.plugin.data import PluginDefinitionConfiguration
    from betty.role import RoleDefinition


def _discover[PluginDefinitionT: PluginDefinition](
    plugins: Iterable[PluginDefinitionConfiguration[PluginDefinitionT]],
) -> Iterable[PluginDefinitionT]:
    for plugin in plugins:
        yield plugin.new_plugin()


@require(Project)
def _discover_copyright_notices(
    project: Project,
) -> Iterable[CopyrightNoticeDefinition]:
    return _discover(project.configuration.copyright_notices)


@require(Project)
def _discover_event_types(project: Project) -> Iterable[EventTypeDefinition]:
    return _discover(project.configuration.event_types)


@require(Project)
def _discover_genders(project: Project) -> Iterable[GenderDefinition]:
    return _discover(project.configuration.genders)


@require(Project)
def _discover_licenses(project: Project) -> Iterable[LicenseDefinition]:
    return _discover(project.configuration.licenses)


@require(Project)
def _discover_place_types(project: Project) -> Iterable[PlaceTypeDefinition]:
    return _discover(project.configuration.place_types)


@require(Project)
def _discover_roles(project: Project) -> Iterable[RoleDefinition]:
    return _discover(project.configuration.roles)
