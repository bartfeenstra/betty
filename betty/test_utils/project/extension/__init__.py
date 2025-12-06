"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import Self, final

import pytest
from typing_extensions import override

from betty.config import Configurable
from betty.project import Project
from betty.project.extension import Extension, ExtensionPlugin
from betty.project.factory import ProjectDependentSelfFactory
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.plugin.dependent import DependentPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase
from betty.typing import private


class ExtensionPluginTestBase(
    HumanFacingPluginDefinitionTestBase,
    DependentPluginDefinitionTestBase,
    OrderedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.project.extension.ExtensionPlugin` implementations.
    """


class ExtensionTestBase:
    """
    A base class for testing :py:class:`betty.project.extension.Extension` implementations.
    """

    @pytest.fixture
    def sut(self) -> Extension:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError


class _DummyExtension(ProjectDependentSelfFactory, Extension):
    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)


@final
@ExtensionPlugin("dummy-one", label="Dummy One")
class DummyExtensionOne(_DummyExtension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


@final
@ExtensionPlugin("dummy-two", label="Dummy Two")
class DummyExtensionTwo(_DummyExtension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


@final
@ExtensionPlugin("dummy-configurable", label="Dummy Configurable")
class DummyConfigurableExtension(Configurable[DummyConfiguration], _DummyExtension):
    """
    A dummy :py:class:`betty.config.Configurable` and :py:class:`betty.project.extension.Extension` implementation.
    """

    @private
    def __init__(self, project: Project):
        super().__init__(configuration=DummyConfiguration(), project=project)
