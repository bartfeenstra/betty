"""
Test utilities for :py:mod:`betty.gender`.
"""

from __future__ import annotations

from betty.gender import Gender
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase


class GenderDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.gender.GenderDefinition` implementations.
    """


class GenderTestBase(PluginTestBase[Gender]):
    """
    A base class for testing :py:class:`betty.gender.Gender` implementations.
    """
