"""
Service levels.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import TypeVar, override

from betty.factory import FactoryError, new_target
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin.repository.provider import PluginRepositoryProvider
from betty.requirement import HasRequirement
from betty.service.container import ServiceContainer

if TYPE_CHECKING:
    from betty.service.level.factory import ServiceLevelTarget

_T = TypeVar("_T")


class ServiceLevel(ServiceContainer, PluginRepositoryProvider):
    """
    A service level.

    A runtime Betty application consists of three types of service containers:

    - :py:class:`betty.app.App`
    - :py:class:`betty.project.Project`
    - :py:class:`betty.project.extension.Extension`

    Extensions always exist in the context of a project, so they are the same level. Additionally, Betty may not be running,
    leaving us with three levels:
    - global (``None``)
    - app (:py:class:`betty.app.App`)
    - project (:py:class:`betty.project.Project`)
    """

    @final
    async def new_target(self, target: ServiceLevelTarget[_T]) -> _T:
        """
        Create a new instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        return await self._new_target(target)

    @final
    @override
    async def _new_target(self, target: ServiceLevelTarget[_T]) -> _T:
        from betty.service.level.factory import (
            ServiceLevelDependentFactory,
            ServiceLevelDependentSelfFactory,
        )

        try:
            if isinstance(target, ServiceLevelDependentFactory):
                return await target.new_for_services(self)
            if isinstance(target, type) and issubclass(
                target, ServiceLevelDependentSelfFactory
            ):
                return await target.new_for_services(self)  # ty:ignore[invalid-return-type]
        except Exception as error:
            if (
                isinstance(target, HasRequirement)
                or isinstance(target, type)
                and issubclass(target, HasRequirement)
            ):
                requirement = await target.requirement(self)
                if requirement is not None:
                    raise FactoryError(
                        requirement.localize(DEFAULT_LOCALIZER)
                    ) from error
            raise
        return await new_target(target)  # ty:ignore[invalid-argument-type]
