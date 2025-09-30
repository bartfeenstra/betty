import pytest
from typing_extensions import override

from betty.ancestry.gender.genders import Female, Male, NonBinary, Unknown
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.gender import GenderDefinitionTestBase


class TestNonBinary(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NonBinary.plugin


class TestFemale(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Female.plugin


class TestMale(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Male.plugin


class TestUnknown(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin
