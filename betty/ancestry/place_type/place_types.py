"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@PlaceTypeDefinition(
    id="borough",
    label=_("Borough"),
)
class Borough(PlaceType):
    """
    A borough.
    """


@final
@PlaceTypeDefinition(
    id="building",
    label=_("Building"),
)
class Building(PlaceType):
    """
    A building.
    """


@final
@PlaceTypeDefinition(
    id="cemetery",
    label=_("Cemetery"),
)
class Cemetery(PlaceType):
    """
    A cemetery.
    """


@final
@PlaceTypeDefinition(
    id="city",
    label=_("City"),
)
class City(PlaceType):
    """
    A city.
    """


@final
@PlaceTypeDefinition(
    id="country",
    label=_("Country"),
)
class Country(PlaceType):
    """
    A country.
    """


@final
@PlaceTypeDefinition(
    id="county",
    label=_("County"),
)
class County(PlaceType):
    """
    A county.
    """


@final
@PlaceTypeDefinition(
    id="department",
    label=_("Department"),
)
class Department(PlaceType):
    """
    A department.
    """


@final
@PlaceTypeDefinition(
    id="district",
    label=_("District"),
)
class District(PlaceType):
    """
    A district.
    """


@final
@PlaceTypeDefinition(
    id="farm",
    label=_("Farm"),
)
class Farm(PlaceType):
    """
    A farm.
    """


@final
@PlaceTypeDefinition(
    id="hamlet",
    label=_("Hamlet"),
)
class Hamlet(PlaceType):
    """
    A hamlet.
    """


@final
@PlaceTypeDefinition(
    id="locality",
    label=_("Locality"),
)
class Locality(PlaceType):
    """
    A locality.
    """


@final
@PlaceTypeDefinition(
    id="municipality",
    label=_("Municipality"),
)
class Municipality(PlaceType):
    """
    A municipality.
    """


@final
@PlaceTypeDefinition(
    id="neighborhood",
    label=_("Neighborhood"),
)
class Neighborhood(PlaceType):
    """
    A neighborhood.
    """


@final
@PlaceTypeDefinition(
    id="number",
    label=_("Number"),
)
class Number(PlaceType):
    """
    A place number, e.g. a house or flat number.
    """


@final
@PlaceTypeDefinition(
    id="parish",
    label=_("Parish"),
)
class Parish(PlaceType):
    """
    A parish.
    """


@final
@PlaceTypeDefinition(
    id="province",
    label=_("Province"),
)
class Province(PlaceType):
    """
    A province.
    """


@final
@PlaceTypeDefinition(
    id="region",
    label=_("Region"),
)
class Region(PlaceType):
    """
    A region.
    """


@final
@PlaceTypeDefinition(
    id="state",
    label=_("State"),
)
class State(PlaceType):
    """
    A state.
    """


@final
@PlaceTypeDefinition(
    id="street",
    label=_("Street"),
)
class Street(PlaceType):
    """
    A street.
    """


@final
@PlaceTypeDefinition(
    id="town",
    label=_("Town"),
)
class Town(PlaceType):
    """
    A town.
    """


@final
@PlaceTypeDefinition(
    id="unknown",
    label=_("Unknown"),
)
class Unknown(PlaceType, Singleton):
    """
    A place of an unknown type.
    """


@final
@PlaceTypeDefinition(
    id="village",
    label=_("Village"),
)
class Village(PlaceType):
    """
    A village.
    """
