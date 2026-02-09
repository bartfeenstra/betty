"""
Test utilities for :py:mod:`betty.extension`.
"""

from typing import Self, final

from typing_extensions import override

from betty.extension import Extension, ExtensionDefinition
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project


class _DummyExtension(Manufacturable, Extension[Project]):
    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(services=project)


@final
@ExtensionDefinition("dummy-one", label="Dummy One")
class DummyExtensionOne(_DummyExtension):
    """
    A dummy :py:class:`betty.extension.Extension` implementation.
    """


@final
@ExtensionDefinition("dummy-two", label="Dummy Two")
class DummyExtensionTwo(_DummyExtension):
    """
    A dummy :py:class:`betty.extension.Extension` implementation.
    """
