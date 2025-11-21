"""
Functionality for creating new instances of types that depend on :py:class:`betty.project.Project`.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.requirement import HasRequirement, Requirement

if TYPE_CHECKING:
    from betty.project import Project
    from betty.service.level import ServiceProviderLevel


class ProjectDependentFactory(HasRequirement):
    """
    Allow this type to be instantiated using a :py:class:`betty.project.Project`.
    """

    @classmethod
    @abstractmethod
    async def new_for_project(cls, project: Project) -> Self:
        """
        Create a new instance using the given project.
        """

    @override
    @classmethod
    async def requirement(cls, services: ServiceProviderLevel, /) -> Requirement | None:
        from betty.project import Project

        return await Project.requirement_for(services, str(cls))
