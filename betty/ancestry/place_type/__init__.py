"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class PlaceType(Mutable, Plugin):
    """
    Define an :py:class:`betty.ancestry.place.Place` type.

    Read more about :doc:`/development/plugin/place-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.place_type.PlaceTypeTestBase`.
    """

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return PlaceType

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "place-type"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Place type")


PLACE_TYPE_REPOSITORY: PluginRepository[PlaceType] = EntryPointPluginRepository(
    PlaceType, "betty.place_type"
)
"""
The place type plugin repository.

Read more about :doc:`/development/plugin/place-type`.
"""
