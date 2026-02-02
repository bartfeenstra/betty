import pytest
from typing_extensions import override

from betty.place_type import PlaceType
from betty.place_type.place_types import (
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
from betty.test_utils.ancestry.place_type import (
    PlaceTypeDefinitionTestBase,
    PlaceTypeTestBase,
)


class TestBoroughDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Borough.plugin()


class TestBorough(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Borough()


class TestBuildingDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Building.plugin()


class TestBuilding(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Building()


class TestCemeteryDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Cemetery.plugin()


class TestCemetery(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Cemetery()


class TestCityDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return City.plugin()


class TestCity(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return City()


class TestCountryDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Country.plugin()


class TestCountry(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Country()


class TestCountyDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return County.plugin()


class TestCounty(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return County()


class TestDepartmentDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Department.plugin()


class TestDepartment(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Department()


class TestDistrictDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return District.plugin()


class TestDistrict(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return District()


class TestFarmDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Farm.plugin()


class TestFarm(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Farm()


class TestHamletDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Hamlet.plugin()


class TestHamlet(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Hamlet()


class TestLocalityDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Locality.plugin()


class TestLocality(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Locality()


class TestMunicipalityDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Municipality.plugin()


class TestMunicipality(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Municipality()


class TestNeighborhoodDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Neighborhood.plugin()


class TestNeighborhood(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Neighborhood()


class TestNumberDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Number.plugin()


class TestNumber(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Number()


class TestParishDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Parish.plugin()


class TestParish(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Parish()


class TestProvinceDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Province.plugin()


class TestProvince(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Province()


class TestRegionDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Region.plugin()


class TestRegion(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Region()


class TestStateDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return State.plugin()


class TestState(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return State()


class TestStreetDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Street.plugin()


class TestStreet(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Street()


class TestTownDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Town.plugin()


class TestTown(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Town()


class TestUnknownDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin()


class TestUnknown(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Unknown()


class TestVillageDefinition(PlaceTypeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Village.plugin()


class TestVillage(PlaceTypeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PlaceType:
        return Village()
