"""
Handle requirements on applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale.localizable.gettext import _
from betty.service.requirement import Requirement, UnmetRequirement

if TYPE_CHECKING:
    from betty.app import App
    from betty.service.level import ServiceLevel


async def _require_app(services: ServiceLevel, target: str, /) -> App:
    from betty.app import App
    from betty.project import Project

    if isinstance(services, Project):
        return services.upstream
    if isinstance(services, App):
        return services
    raise UnmetRequirement(_("{target} requires a running app.").format(target=target))


require_app = Requirement(_require_app)
