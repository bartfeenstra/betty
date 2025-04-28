"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class PlaceType(Mutable, Plugin):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.place_type.PlaceTypeTestBase`.
    """


PLACE_TYPE_REPOSITORY: PluginRepository[PlaceType] = EntryPointPluginRepository(
    "betty.place_type"
)
"""
The place type plugin repository.

Read more about :doc:`/development/plugin/place-type`.
"""
