"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    UserFacingPluginDefinitionTestBase,
)


class GenderDefinitionTestBase(
    UserFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.gender.GenderDefinition` implementations.
    """
