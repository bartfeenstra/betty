"""
Test utilities for :py:mod:`betty.ancestry.place_type`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    HumanFacingPluginDefinitionTestBase,
)


class PlaceTypeDefinitionTestBase(
    HumanFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.place_type.PlaceTypeDefinition` implementations.
    """
