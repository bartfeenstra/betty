"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import Self, final

import pytest
from typing_extensions import override

from betty.app import App
from betty.config import Configurable
from betty.locale.localizable import Plain
from betty.project import Project
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.plugin.classed import ClassedPluginDefinitionTestBase
from betty.test_utils.plugin.dependent import DependentPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class ExtensionDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
    DependentPluginDefinitionTestBase,
    OrderedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.project.extension.ExtensionDefinition` implementations.
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

    async def test_new_for_project(self, temporary_app: App, sut: Extension) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.new_for_project` implementations.
        """
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await type(sut).new_for_project(project)
            assert sut.project == project


@final
@ExtensionDefinition(
    id="dummy-one",
    label=Plain(""),
)
class DummyExtensionOne(Extension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


@final
@ExtensionDefinition(
    id="dummy-two",
    label=Plain(""),
)
class DummyExtensionTwo(Extension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


@final
@ExtensionDefinition(
    id="dummy-configurable",
    label=Plain(""),
)
class DummyConfigurableExtension(Configurable[DummyConfiguration], Extension):
    """
    A dummy :py:class:`betty.config.Configurable` and :py:class:`betty.project.extension.Extension` implementation.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project, configuration=DummyConfiguration())
