"""
Handle requirements on projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale.localizable.gettext import _
from betty.service.requirement import Requirement, UnmetRequirement

if TYPE_CHECKING:
    from betty.project import Project
    from betty.service.level import ServiceLevel


async def _require_project(services: ServiceLevel, target: str, /) -> Project:
    from betty.project import Project

    if isinstance(services, Project):
        return services
    raise UnmetRequirement(_("{target} requires a project.").format(target=target))


require_project = Requirement(_require_project)
