from __future__ import annotations

from typing import TYPE_CHECKING

from betty.copyright_notice import CopyrightNoticeDefinition
from betty.event_type import EventTypeDefinition
from betty.gender import GenderDefinition
from betty.license import LicenseDefinition
from betty.place_type import PlaceTypeDefinition
from betty.project import Project
from betty.role import RoleDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable


@Project.require
def _discover_copyright_notices(
    project: Project,
) -> Iterable[CopyrightNoticeDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, CopyrightNoticeDefinition)
    )


@Project.require
def _discover_event_types(project: Project) -> Iterable[EventTypeDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, EventTypeDefinition)
    )


@Project.require
def _discover_genders(project: Project) -> Iterable[GenderDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, GenderDefinition)
    )


@Project.require
def _discover_licenses(project: Project) -> Iterable[LicenseDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, LicenseDefinition)
    )


@Project.require
def _discover_place_types(project: Project) -> Iterable[PlaceTypeDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, PlaceTypeDefinition)
    )


@Project.require
def _discover_roles(project: Project) -> Iterable[RoleDefinition]:
    return (
        plugin
        for plugin in project._plugin_discoveries
        if isinstance(plugin, RoleDefinition)
    )
