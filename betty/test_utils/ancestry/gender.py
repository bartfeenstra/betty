"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.ancestry.gender import Gender
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase


class GenderDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.ancestry.gender.GenderDefinition` implementations.
    """


class GenderTestBase(PluginTestBase[Gender]):
    """
    A base class for testing :py:class:`betty.ancestry.gender.Gender` implementations.
    """
