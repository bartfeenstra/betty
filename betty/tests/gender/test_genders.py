import pytest
from typing_extensions import override

from betty.gender import Gender
from betty.gender.genders import Man, NonBinary, Unknown, Woman
from betty.plugin import PluginDefinition
from betty.test_utils.ancestry.gender import GenderDefinitionTestBase, GenderTestBase


class TestNonBinaryDefinition(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return NonBinary.plugin()


class TestNonBinary(GenderTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Gender:
        return NonBinary()


class TestWomanDefinition(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Woman.plugin()


class TestWoman(GenderTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Gender:
        return Woman()


class TestManDefinition(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Man.plugin()


class TestMan(GenderTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Gender:
        return Man()


class TestUnknownDefinition(GenderDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Unknown.plugin()


class TestUnknown(GenderTestBase):
    @override
    @pytest.fixture
    def sut(self) -> Gender:
        return Unknown()
