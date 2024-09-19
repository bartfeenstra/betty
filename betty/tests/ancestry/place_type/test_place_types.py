from typing_extensions import override

from betty.ancestry.place_type.place_types import (
    Borough,
    Building,
    City,
    Country,
    County,
    Department,
    District,
    Farm,
    Hamlet,
    Locality,
    Municipality,
    Neighborhood,
    Number,
    Parish,
    Province,
    Region,
    State,
    Street,
    Town,
    Unknown,
    Village,
)
from betty.test_utils.ancestry.place_type import PlaceTypeTestBase


class TestBorough(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Borough]:
        return Borough


class TestBuilding(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Building]:
        return Building


class TestCity(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[City]:
        return City


class TestCountry(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Country]:
        return Country


class TestCounty(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[County]:
        return County


class TestDepartment(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Department]:
        return Department


class TestDistrict(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[District]:
        return District


class TestFarm(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Farm]:
        return Farm


class TestHamlet(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Hamlet]:
        return Hamlet


class TestLocality(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Locality]:
        return Locality


class TestMunicipality(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Municipality]:
        return Municipality


class TestNeighborhood(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Neighborhood]:
        return Neighborhood


class TestNumber(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Number]:
        return Number


class TestParish(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Parish]:
        return Parish


class TestProvince(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Province]:
        return Province


class TestRegion(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Region]:
        return Region


class TestState(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[State]:
        return State


class TestStreet(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Street]:
        return Street


class TestTown(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Town]:
        return Town


class TestUnknown(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Unknown]:
        return Unknown


class TestVillage(PlaceTypeTestBase):
    @override
    def get_sut_class(self) -> type[Village]:
        return Village
