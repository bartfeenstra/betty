"""
Provide Betty's ancestry place types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.place_type import PlaceType, PlaceTypeDefinition
from betty.classtools import Singleton
from betty.locale.localizable import _


@final
@PlaceTypeDefinition("borough", label=_("Borough"))
class Borough(PlaceType):
    """
    A borough.
    """


@final
@PlaceTypeDefinition("building", label=_("Building"))
class Building(PlaceType):
    """
    A building.
    """


@final
@PlaceTypeDefinition("cemetery", label=_("Cemetery"))
class Cemetery(PlaceType):
    """
    A cemetery.
    """


@final
@PlaceTypeDefinition("city", label=_("City"))
class City(PlaceType):
    """
    A city.
    """


@final
@PlaceTypeDefinition("country", label=_("Country"))
class Country(PlaceType):
    """
    A country.
    """


@final
@PlaceTypeDefinition("county", label=_("County"))
class County(PlaceType):
    """
    A county.
    """


@final
@PlaceTypeDefinition("department", label=_("Department"))
class Department(PlaceType):
    """
    A department.
    """


@final
@PlaceTypeDefinition("district", label=_("District"))
class District(PlaceType):
    """
    A district.
    """


@final
@PlaceTypeDefinition("farm", label=_("Farm"))
class Farm(PlaceType):
    """
    A farm.
    """


@final
@PlaceTypeDefinition("hamlet", label=_("Hamlet"))
class Hamlet(PlaceType):
    """
    A hamlet.
    """


@final
@PlaceTypeDefinition("locality", label=_("Locality"))
class Locality(PlaceType):
    """
    A locality.
    """


@final
@PlaceTypeDefinition("municipality", label=_("Municipality"))
class Municipality(PlaceType):
    """
    A municipality.
    """


@final
@PlaceTypeDefinition("neighborhood", label=_("Neighborhood"))
class Neighborhood(PlaceType):
    """
    A neighborhood.
    """


@final
@PlaceTypeDefinition("number", label=_("Number"))
class Number(PlaceType):
    """
    A place number, e.g. a house or flat number.
    """


@final
@PlaceTypeDefinition("parish", label=_("Parish"))
class Parish(PlaceType):
    """
    A parish.
    """


@final
@PlaceTypeDefinition("province", label=_("Province"))
class Province(PlaceType):
    """
    A province.
    """


@final
@PlaceTypeDefinition("region", label=_("Region"))
class Region(PlaceType):
    """
    A region.
    """


@final
@PlaceTypeDefinition("state", label=_("State"))
class State(PlaceType):
    """
    A state.
    """


@final
@PlaceTypeDefinition("street", label=_("Street"))
class Street(PlaceType):
    """
    A street.
    """


@final
@PlaceTypeDefinition("town", label=_("Town"))
class Town(PlaceType):
    """
    A town.
    """


@final
@PlaceTypeDefinition("unknown", label=_("Unknown"))
class Unknown(PlaceType, Singleton):
    """
    A place of an unknown type.
    """


@final
@PlaceTypeDefinition("village", label=_("Village"))
class Village(PlaceType):
    """
    A village.
    """
