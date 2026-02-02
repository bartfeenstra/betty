"""
Test utilities for :py:mod:`betty.place_type`.
"""

from __future__ import annotations

from betty.place_type import PlaceType
from betty.test_utils.definition.human_facing import HumanFacingDefinitionTestBase
from betty.test_utils.plugin import PluginTestBase


class PlaceTypeDefinitionTestBase(HumanFacingDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.place_type.PlaceTypeDefinition` implementations.
    """


class PlaceTypeTestBase(PluginTestBase[PlaceType]):
    """
    A base class for testing :py:class:`betty.place_type.PlaceType` implementations.
    """
