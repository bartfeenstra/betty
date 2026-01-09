from collections.abc import Iterable
from typing import cast

import pytest
from typing_extensions import override

from betty.model.schema import ToManySchema, ToOneSchema, ToZeroOrOneSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


class TestToOneSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        return [
            (
                ToOneSchema(),
                [
                    "https://example.com",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut_data(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestToZeroOrOneSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        return [
            (
                ToZeroOrOneSchema(),
                [
                    "https://example.com",
                    None,
                ],
                [True, False, 123, [], {}],
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut_data(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestToManySchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        return [
            (
                ToManySchema(),
                [
                    [],
                    ["https://example.com"],
                ],
                [True, False, None, "123", 123, {}],
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut_data(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)
