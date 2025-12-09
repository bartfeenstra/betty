"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.ancestry.gender import Gender
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class GenderDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.ancestry.gender.GenderDefinition` implementations.
    """


class GenderTestBase(PluginTestBase[Gender]):
    """
    A base class for testing :py:class:`betty.ancestry.gender.Gender` implementations.
    """
