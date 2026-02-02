"""
Test utilities for :py:mod:`betty.extension`.
"""

from typing import Self, final

from typing_extensions import override

from betty.extension import Extension, ExtensionDefinition
from betty.project import Project
from betty.service.level import Manufacturable
from betty.service.requirement.project import require_project
from betty.test_utils.config import DummyConfigurable
from betty.test_utils.data import DummyData
from betty.typing import private


class _DummyExtension(Manufacturable, Extension):
    @override
    @classmethod
    @require_project
    async def new_for_services(cls, *, project: Project) -> Self:
        return cls(project=project)


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


@final
@ExtensionDefinition("dummy-configurable", label="Dummy Configurable")
class DummyConfigurableExtension(DummyConfigurable, _DummyExtension):
    """
    A dummy :py:class:`betty.config.Configurable` and :py:class:`betty.extension.Extension` implementation.
    """

    @private
    def __init__(self, project: Project):
        super().__init__(configuration=DummyData(), project=project)
