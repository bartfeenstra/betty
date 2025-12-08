import pytest
from typing_extensions import override

from betty.ancestry.gender.genders import Man, NonBinary, Unknown, Woman
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.gender import GenderPluginTestBase


class TestNonBinary(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NonBinary.plugin


class TestWoman(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Woman.plugin


class TestMan(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Man.plugin


class TestUnknown(GenderPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin
