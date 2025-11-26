"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.place_type import PlaceType, PlaceTypePlugin
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@PlaceTypePlugin("borough", label=_("Borough"))
class Borough(PlaceType):
    """
    A borough.
    """


@final
@PlaceTypePlugin("building", label=_("Building"))
class Building(PlaceType):
    """
    A building.
    """


@final
@PlaceTypePlugin("cemetery", label=_("Cemetery"))
class Cemetery(PlaceType):
    """
    A cemetery.
    """


@final
@PlaceTypePlugin("city", label=_("City"))
class City(PlaceType):
    """
    A city.
    """


@final
@PlaceTypePlugin("country", label=_("Country"))
class Country(PlaceType):
    """
    A country.
    """


@final
@PlaceTypePlugin("county", label=_("County"))
class County(PlaceType):
    """
    A county.
    """


@final
@PlaceTypePlugin("department", label=_("Department"))
class Department(PlaceType):
    """
    A department.
    """


@final
@PlaceTypePlugin("district", label=_("District"))
class District(PlaceType):
    """
    A district.
    """


@final
@PlaceTypePlugin("farm", label=_("Farm"))
class Farm(PlaceType):
    """
    A farm.
    """


@final
@PlaceTypePlugin("hamlet", label=_("Hamlet"))
class Hamlet(PlaceType):
    """
    A hamlet.
    """


@final
@PlaceTypePlugin("locality", label=_("Locality"))
class Locality(PlaceType):
    """
    A locality.
    """


@final
@PlaceTypePlugin("municipality", label=_("Municipality"))
class Municipality(PlaceType):
    """
    A municipality.
    """


@final
@PlaceTypePlugin("neighborhood", label=_("Neighborhood"))
class Neighborhood(PlaceType):
    """
    A neighborhood.
    """


@final
@PlaceTypePlugin("number", label=_("Number"))
class Number(PlaceType):
    """
    A place number, e.g. a house or flat number.
    """


@final
@PlaceTypePlugin("parish", label=_("Parish"))
class Parish(PlaceType):
    """
    A parish.
    """


@final
@PlaceTypePlugin("province", label=_("Province"))
class Province(PlaceType):
    """
    A province.
    """


@final
@PlaceTypePlugin("region", label=_("Region"))
class Region(PlaceType):
    """
    A region.
    """


@final
@PlaceTypePlugin("state", label=_("State"))
class State(PlaceType):
    """
    A state.
    """


@final
@PlaceTypePlugin("street", label=_("Street"))
class Street(PlaceType):
    """
    A street.
    """


@final
@PlaceTypePlugin("town", label=_("Town"))
class Town(PlaceType):
    """
    A town.
    """


@final
@PlaceTypePlugin("unknown", label=_("Unknown"))
class Unknown(PlaceType, Singleton):
    """
    A place of an unknown type.
    """


@final
@PlaceTypePlugin("village", label=_("Village"))
class Village(PlaceType):
    """
    A village.
    """
