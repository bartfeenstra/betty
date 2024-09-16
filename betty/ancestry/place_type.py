"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations


from betty.locale.localizable import _
from betty.plugin import Plugin, PluginRepository, PluginShorthandBase
from betty.plugin.entry_point import EntryPointPluginRepository


class PlaceType(Plugin):
    """
    Define an :py:class:`betty.ancestry.Place` type.

    Read more about :doc:`/development/plugin/place-type`.

    To test your own subclasses, use :py:class:`betty.test_utils.ancestry.place_type.PlaceTypeTestBase`.
    """

    pass


PLACE_TYPE_REPOSITORY: PluginRepository[PlaceType] = EntryPointPluginRepository(
    "betty.place_type"
)
"""
The place type plugin repository.

Read more about :doc:`/development/plugin/place-type`.
"""


class Borough(PluginShorthandBase, PlaceType):
    """
    A borough.
    """

    _plugin_id = "borough"
    _plugin_label = _("Borough")


class Building(PluginShorthandBase, PlaceType):
    """
    A building.
    """

    _plugin_id = "building"
    _plugin_label = _("Building")


class City(PluginShorthandBase, PlaceType):
    """
    A city.
    """

    _plugin_id = "city"
    _plugin_label = _("City")


class Country(PluginShorthandBase, PlaceType):
    """
    A country.
    """

    _plugin_id = "country"
    _plugin_label = _("Country")


class County(PluginShorthandBase, PlaceType):
    """
    A county.
    """

    _plugin_id = "county"
    _plugin_label = _("County")


class Department(PluginShorthandBase, PlaceType):
    """
    A department.
    """

    _plugin_id = "department"
    _plugin_label = _("Department")


class District(PluginShorthandBase, PlaceType):
    """
    A district.
    """

    _plugin_id = "district"
    _plugin_label = _("District")


class Farm(PluginShorthandBase, PlaceType):
    """
    A farm.
    """

    _plugin_id = "farm"
    _plugin_label = _("Farm")


class Hamlet(PluginShorthandBase, PlaceType):
    """
    A hamlet.
    """

    _plugin_id = "hamlet"
    _plugin_label = _("Hamlet")


class Locality(PluginShorthandBase, PlaceType):
    """
    A locality.
    """

    _plugin_id = "locality"
    _plugin_label = _("Locality")


class Municipality(PluginShorthandBase, PlaceType):
    """
    A municipality.
    """

    _plugin_id = "municipality"
    _plugin_label = _("Municipality")


class Neighborhood(PluginShorthandBase, PlaceType):
    """
    A neighborhood.
    """

    _plugin_id = "neighborhood"
    _plugin_label = _("Neighborhood")


class Number(PluginShorthandBase, PlaceType):
    """
    A place number, e.g. a house or flat number.
    """

    _plugin_id = "number"
    _plugin_label = _("Number")


class Parish(PluginShorthandBase, PlaceType):
    """
    A parish.
    """

    _plugin_id = "parish"
    _plugin_label = _("Parish")


class Province(PluginShorthandBase, PlaceType):
    """
    A province.
    """

    _plugin_id = "province"
    _plugin_label = _("Province")


class Region(PluginShorthandBase, PlaceType):
    """
    A region.
    """

    _plugin_id = "region"
    _plugin_label = _("Region")


class State(PluginShorthandBase, PlaceType):
    """
    A state.
    """

    _plugin_id = "state"
    _plugin_label = _("State")


class Street(PluginShorthandBase, PlaceType):
    """
    A street.
    """

    _plugin_id = "street"
    _plugin_label = _("Street")


class Town(PluginShorthandBase, PlaceType):
    """
    A town.
    """

    _plugin_id = "town"
    _plugin_label = _("Town")


class Unknown(PluginShorthandBase, PlaceType):
    """
    A place of an unknown type.
    """

    _plugin_id = "unknown"
    _plugin_label = _("Unknown")


class Village(PluginShorthandBase, PlaceType):
    """
    A village.
    """

    _plugin_id = "village"
    _plugin_label = _("Village")
