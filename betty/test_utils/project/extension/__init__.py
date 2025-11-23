"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import final

import pytest

from betty.config import Configurable
from betty.locale.localizable import Plain
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.plugin.classed import ClassedPluginDefinitionTestBase
from betty.test_utils.plugin.dependent import DependentPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase
from betty.typing import private


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

    @private
    def __init__(self):
        super().__init__(configuration=DummyConfiguration())
