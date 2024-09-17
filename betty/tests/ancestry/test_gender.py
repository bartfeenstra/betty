from typing_extensions import override

from betty.ancestry.gender import NonBinary, Female, Male, Unknown
from betty.test_utils.ancestry.gender import GenderTestBase


class TestNonBinary(GenderTestBase):
    @override
    def get_sut_class(self) -> type[NonBinary]:
        return NonBinary


class TestFemale(GenderTestBase):
    @override
    def get_sut_class(self) -> type[Female]:
        return Female


class TestMale(GenderTestBase):
    @override
    def get_sut_class(self) -> type[Male]:
        return Male


class TestUnknown(GenderTestBase):
    @override
    def get_sut_class(self) -> type[Unknown]:
        return Unknown
