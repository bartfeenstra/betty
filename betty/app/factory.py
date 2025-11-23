"""
Functionality for creating new instances of types that depend on :py:class:`betty.app.App`.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Self

from typing_extensions import override

from betty.requirement import HasRequirement, Requirement

if TYPE_CHECKING:
    from betty.app import App
    from betty.service.level import ServiceLevel


class AppDependentFactory(HasRequirement):
    """
    Allow this type to be instantiated using a :py:class:`betty.app.App`.
    """

    @classmethod
    @abstractmethod
    async def new_for_app(cls, app: App) -> Self:
        """
        Create a new instance using the given app.
        """

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        from betty.app import App

        return await App.requirement_for(services, str(cls))
