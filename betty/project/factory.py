"""
Functionality for creating new instances of types that depend on :py:class:`betty.project.Project`.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Generic,
    Self,
    TypeAlias,
    TypeVar,
    final,
)

from typing_extensions import override

from betty.app.factory import AppTarget
from betty.asyncio import ensure_await
from betty.requirement import HasRequirement, Requirement

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from betty.project import Project
    from betty.service.level import ServiceLevel


_T = TypeVar("_T")


class ProjectDependentSelfFactory(HasRequirement):
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


class ProjectDependentFactory(Generic[_T]):
    """
    Create new instances using a :py:class:`betty.project.Project`.
    """

    @abstractmethod
    async def new_for_project(self, project: Project, /) -> _T:
        """
        Create a new instance using the given project.
        """


@final
class CallbackProjectDependentFactory(ProjectDependentFactory[_T], Generic[_T]):
    """
    Create new instances using a callback that takes a :py:class:`betty.project.Project`.
    """

    def __init__(
        self, callback: Callable[[Project], Awaitable[_T]] | Callable[[Project], _T], /
    ):
        self._callback = callback

    @override
    async def new_for_project(self, project: Project, /) -> _T:
        return await ensure_await(self._callback(project))


ProjectTarget: TypeAlias = (
    AppTarget[_T] | ProjectDependentSelfFactory | ProjectDependentFactory[_T]
)
"""
#. If ``target`` subclasses :py:class:`betty.app.project.ProjectDependentSelfFactory`, this will return ``target``'s
   ``new_for_project()``'s return value.
#. If ``target`` is an instance of :py:class:`betty.app.project.ProjectDependentFactory`, this will return ``target``'s
   ``new_for_project()``'s return value.
#. Else, ``target`` will be treated as :py:type:`betty.app.factory.AppFactoryTarget`.
"""
