import pytest
from typing_extensions import override

from betty.ancestry.gender.genders import Female, Male, NonBinary, Unknown
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.gender import GenderPluginTestBase


class TestNonBinary(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NonBinary.plugin


class TestFemale(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Female.plugin


class TestMale(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Male.plugin


class TestUnknown(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin
