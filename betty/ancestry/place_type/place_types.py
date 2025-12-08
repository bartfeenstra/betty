"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.place_type import PlaceType, PlaceTypePlugin
from betty.classtools import Singleton
from betty.locale.localizable import _, ngettext


@final
@PlaceTypePlugin(
    "borough",
    label=_("Borough"),
    label_plural=_("Boroughs"),
    label_countable=ngettext("{count} borough", "{count} boroughs"),
)
class Borough(PlaceType):
    """
    A borough.
    """


@final
@PlaceTypePlugin(
    "building",
    label=_("Building"),
    label_plural=_("Buildings"),
    label_countable=ngettext("{count} building", "{count} buildings"),
)
class Building(PlaceType):
    """
    A building.
    """


@final
@PlaceTypePlugin(
    "cemetery",
    label=_("Cemetery"),
    label_plural=_("Cemeteries"),
    label_countable=ngettext("{count} cemetery", "{count} cemeteries"),
)
class Cemetery(PlaceType):
    """
    A cemetery.
    """


@final
@PlaceTypePlugin(
    "city",
    label=_("City"),
    label_plural=_("Cities"),
    label_countable=ngettext("{count} city", "{count} cities"),
)
class City(PlaceType):
    """
    A city.
    """


@final
@PlaceTypePlugin(
    "country",
    label=_("Country"),
    label_plural=_(""),
    label_countable=ngettext("{count} ", "{count} "),
)
class Country(PlaceType):
    """
    A country.
    """


@final
@PlaceTypePlugin(
    "county",
    label=_("County"),
    label_plural=_("Counties"),
    label_countable=ngettext("{count} county", "{count} counties"),
)
class County(PlaceType):
    """
    A county.
    """


@final
@PlaceTypePlugin(
    "department",
    label=_("Department"),
    label_plural=_("Departments"),
    label_countable=ngettext("{count} department", "{count} departments"),
)
class Department(PlaceType):
    """
    A department.
    """


@final
@PlaceTypePlugin(
    "district",
    label=_("District"),
    label_plural=_("Districts"),
    label_countable=ngettext("{count} district", "{count} districts"),
)
class District(PlaceType):
    """
    A district.
    """


@final
@PlaceTypePlugin(
    "farm",
    label=_("Farm"),
    label_plural=_("Farms"),
    label_countable=ngettext("{count} farm", "{count} farms"),
)
class Farm(PlaceType):
    """
    A farm.
    """


@final
@PlaceTypePlugin(
    "hamlet",
    label=_("Hamlet"),
    label_plural=_("Hamlets"),
    label_countable=ngettext("{count} hamlet", "{count} hamlets"),
)
class Hamlet(PlaceType):
    """
    A hamlet.
    """


@final
@PlaceTypePlugin(
    "locality",
    label=_("Locality"),
    label_plural=_("Localities"),
    label_countable=ngettext("{count} locality", "{count} localities"),
)
class Locality(PlaceType):
    """
    A locality.
    """


@final
@PlaceTypePlugin(
    "municipality",
    label=_("Municipality"),
    label_plural=_("Municipalities"),
    label_countable=ngettext("{count} municipality", "{count} municipalities"),
)
class Municipality(PlaceType):
    """
    A municipality.
    """


@final
@PlaceTypePlugin(
    "neighborhood",
    label=_("Neighborhood"),
    label_plural=_("Neighborhoods"),
    label_countable=ngettext("{count} neighborhood", "{count} neighborhoods"),
)
class Neighborhood(PlaceType):
    """
    A neighborhood.
    """


@final
@PlaceTypePlugin(
    "number",
    label=_("Number"),
    label_plural=_("Numbers"),
    label_countable=ngettext("{count} number", "{count} numbers"),
)
class Number(PlaceType):
    """
    A place number, e.g. a house or flat number.
    """


@final
@PlaceTypePlugin(
    "parish",
    label=_("Parish"),
    label_plural=_("Parishes"),
    label_countable=ngettext("{count} parish", "{count} parishes"),
)
class Parish(PlaceType):
    """
    A parish.
    """


@final
@PlaceTypePlugin(
    "province",
    label=_("Province"),
    label_plural=_("Provinces"),
    label_countable=ngettext("{count} province", "{count} provinces"),
)
class Province(PlaceType):
    """
    A province.
    """


@final
@PlaceTypePlugin(
    "region",
    label=_("Region"),
    label_plural=_("Regions"),
    label_countable=ngettext("{count} region", "{count} regions"),
)
class Region(PlaceType):
    """
    A region.
    """


@final
@PlaceTypePlugin(
    "state",
    label=_("State"),
    label_plural=_("States"),
    label_countable=ngettext("{count} state", "{count} states"),
)
class State(PlaceType):
    """
    A state.
    """


@final
@PlaceTypePlugin(
    "street",
    label=_("Street"),
    label_plural=_("Streets"),
    label_countable=ngettext("{count} street", "{count} streets"),
)
class Street(PlaceType):
    """
    A street.
    """


@final
@PlaceTypePlugin(
    "town",
    label=_("Town"),
    label_plural=_("Towns"),
    label_countable=ngettext("{count} town", "{count} towns"),
)
class Town(PlaceType):
    """
    A town.
    """


@final
@PlaceTypePlugin(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(PlaceType, Singleton):
    """
    A place of an unknown type.
    """


@final
@PlaceTypePlugin(
    "village",
    label=_("Village"),
    label_plural=_("Villages"),
    label_countable=ngettext("{count} village", "{count} villages"),
)
class Village(PlaceType):
    """
    A village.
    """
