"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.place_type import PlaceType, PlaceTypePlugin
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@PlaceTypePlugin(
    id="borough",
    label=_("Borough"),
)
class Borough(PlaceType):
    """
    A borough.
    """


@final
@PlaceTypePlugin(
    id="building",
    label=_("Building"),
)
class Building(PlaceType):
    """
    A building.
    """


@final
@PlaceTypePlugin(
    id="cemetery",
    label=_("Cemetery"),
)
class Cemetery(PlaceType):
    """
    A cemetery.
    """


@final
@PlaceTypePlugin(
    id="city",
    label=_("City"),
)
class City(PlaceType):
    """
    A city.
    """


@final
@PlaceTypePlugin(
    id="country",
    label=_("Country"),
)
class Country(PlaceType):
    """
    A country.
    """


@final
@PlaceTypePlugin(
    id="county",
    label=_("County"),
)
class County(PlaceType):
    """
    A county.
    """


@final
@PlaceTypePlugin(
    id="department",
    label=_("Department"),
)
class Department(PlaceType):
    """
    A department.
    """


@final
@PlaceTypePlugin(
    id="district",
    label=_("District"),
)
class District(PlaceType):
    """
    A district.
    """


@final
@PlaceTypePlugin(
    id="farm",
    label=_("Farm"),
)
class Farm(PlaceType):
    """
    A farm.
    """


@final
@PlaceTypePlugin(
    id="hamlet",
    label=_("Hamlet"),
)
class Hamlet(PlaceType):
    """
    A hamlet.
    """


@final
@PlaceTypePlugin(
    id="locality",
    label=_("Locality"),
)
class Locality(PlaceType):
    """
    A locality.
    """


@final
@PlaceTypePlugin(
    id="municipality",
    label=_("Municipality"),
)
class Municipality(PlaceType):
    """
    A municipality.
    """


@final
@PlaceTypePlugin(
    id="neighborhood",
    label=_("Neighborhood"),
)
class Neighborhood(PlaceType):
    """
    A neighborhood.
    """


@final
@PlaceTypePlugin(
    id="number",
    label=_("Number"),
)
class Number(PlaceType):
    """
    A place number, e.g. a house or flat number.
    """


@final
@PlaceTypePlugin(
    id="parish",
    label=_("Parish"),
)
class Parish(PlaceType):
    """
    A parish.
    """


@final
@PlaceTypePlugin(
    id="province",
    label=_("Province"),
)
class Province(PlaceType):
    """
    A province.
    """


@final
@PlaceTypePlugin(
    id="region",
    label=_("Region"),
)
class Region(PlaceType):
    """
    A region.
    """


@final
@PlaceTypePlugin(
    id="state",
    label=_("State"),
)
class State(PlaceType):
    """
    A state.
    """


@final
@PlaceTypePlugin(
    id="street",
    label=_("Street"),
)
class Street(PlaceType):
    """
    A street.
    """


@final
@PlaceTypePlugin(
    id="town",
    label=_("Town"),
)
class Town(PlaceType):
    """
    A town.
    """


@final
@PlaceTypePlugin(
    id="unknown",
    label=_("Unknown"),
)
class Unknown(PlaceType, Singleton):
    """
    A place of an unknown type.
    """


@final
@PlaceTypePlugin(
    id="village",
    label=_("Village"),
)
class Village(PlaceType):
    """
    A village.
    """
