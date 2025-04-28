"""
Test utilities for :py:mod:`betty.ancestry.place_type`.
"""

from __future__ import annotations

from betty.ancestry.place_type import PlaceType
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginTestBase,
)


class PlaceTypeTestBase(PluginTestBase[PlaceType]):
    """
    A base class for testing :py:class:`betty.ancestry.place_type.PlaceType` implementations.
    """


class DummyPlaceType(DummyPlugin, PlaceType):
    """
    A dummy place type implementation.
    """
