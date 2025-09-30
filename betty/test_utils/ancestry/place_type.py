"""
Test utilities for :py:mod:`betty.ancestry.place_type`.
"""

from __future__ import annotations

from betty.test_utils.plugin import (
    ClassedPluginDefinitionTestBase,
    UserFacingPluginDefinitionTestBase,
)


class PlaceTypeDefinitionTestBase(
    UserFacingPluginDefinitionTestBase,
    ClassedPluginDefinitionTestBase,
):
    """
    A base class for testing :py:class:`betty.ancestry.place_type.PlaceTypeDefinition` implementations.
    """
