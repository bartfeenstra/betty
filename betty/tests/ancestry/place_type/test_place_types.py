import pytest
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
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.place_type import PlaceTypeDefinitionTestBase


class TestBorough(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Borough.plugin


class TestBuilding(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Building.plugin


class TestCity(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return City.plugin


class TestCountry(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Country.plugin


class TestCounty(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return County.plugin


class TestDepartment(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Department.plugin


class TestDistrict(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return District.plugin


class TestFarm(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Farm.plugin


class TestHamlet(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Hamlet.plugin


class TestLocality(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Locality.plugin


class TestMunicipality(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Municipality.plugin


class TestNeighborhood(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Neighborhood.plugin


class TestNumber(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Number.plugin


class TestParish(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Parish.plugin


class TestProvince(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Province.plugin


class TestRegion(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Region.plugin


class TestState(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return State.plugin


class TestStreet(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Street.plugin


class TestTown(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Town.plugin


class TestUnknown(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin


class TestVillage(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Village.plugin
