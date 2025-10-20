"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)


class GenderDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.gender.GenderDefinition` implementations.
    """
