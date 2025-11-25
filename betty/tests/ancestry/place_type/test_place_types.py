import pytest
from typing_extensions import override

from betty.ancestry.place_type.place_types import (
    Borough,
    Building,
    Cemetery,
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
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.place_type import PlaceTypePluginTestBase


class TestBorough(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Borough.plugin


class TestBuilding(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Building.plugin


class TestCemetery(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Cemetery.plugin


class TestCity(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return City.plugin


class TestCountry(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Country.plugin


class TestCounty(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return County.plugin


class TestDepartment(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Department.plugin


class TestDistrict(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return District.plugin


class TestFarm(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Farm.plugin


class TestHamlet(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Hamlet.plugin


class TestLocality(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Locality.plugin


class TestMunicipality(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Municipality.plugin


class TestNeighborhood(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Neighborhood.plugin


class TestNumber(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Number.plugin


class TestParish(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Parish.plugin


class TestProvince(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Province.plugin


class TestRegion(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Region.plugin


class TestState(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return State.plugin


class TestStreet(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Street.plugin


class TestTown(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Town.plugin


class TestUnknown(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin


class TestVillage(PlaceTypePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Village.plugin
