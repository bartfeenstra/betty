"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import final

import pytest
from typing_extensions import override

from betty.app import App
from betty.locale.localizable import Plain
from betty.project import Project
from betty.project.extension import (
    ConfigurableExtension,
    Extension,
    ExtensionDefinition,
)
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)
from betty.test_utils.plugin.dependent import DependentPluginDefinitionTestBase
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
    id="dummy",
    label=Plain(""),
)
class DummyExtension(Extension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


@final
@ExtensionDefinition(
    id="dummy-configurable",
    label=Plain(""),
)
class DummyConfigurableExtension(ConfigurableExtension[DummyConfiguration]):
    """
    A dummy :py:class:`betty.project.extension.ConfigurableExtension` implementation.
    """

    @override
    @classmethod
    def new_default_configuration(cls) -> DummyConfiguration:
        return DummyConfiguration()
