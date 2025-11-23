"""
Functionality for creating new instances of types that depend on :py:class:`betty.project.Project`.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self, TypeAlias, TypeVar

from typing_extensions import override

from betty.app.factory import AppFactoryTarget
from betty.requirement import HasRequirement, Requirement

if TYPE_CHECKING:
    from betty.project import Project
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")


class ProjectDependentFactory(HasRequirement):
    """
    Allow this type to be instantiated using a :py:class:`betty.project.Project`.
    """

    @classmethod
    @abstractmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        """
        Create a new instance using the given project.
        """

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        from betty.project import Project

        return await Project.requirement_for(services, str(cls))


ProjectFactoryTarget: TypeAlias = AppFactoryTarget[_T] | ProjectDependentFactory
"""
#. If ``target`` subclasses :py:class:`betty.app.project.ProjectDependentFactory`, this will call return ``target``'s
   ``new_for_project()``'s return value.
#. Else, ``target`` will be treated as :py:type:`betty.app.factory.AppFactoryTarget`.
"""
