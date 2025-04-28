"""
Functionality for creating new instances of types that depend on :py:class:`betty.project.Project`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from betty.project import Project


class ProjectDependentFactory(ABC):
    """
    Allow this type to be instantiated using a :py:class:`betty.project.Project`.
    """

    @classmethod
    @abstractmethod
    async def new_for_project(cls, project: Project) -> Self:
        """
        Create a new instance using the given project.
        """
