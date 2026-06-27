from __future__ import annotations

from typing import override

import pytest

from betty.json_schemas.date import DateExpressionSchema, DateRangeSchema, DateSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut
from betty.tests.test_date import (
    date_dumps,
    dummy_date_expression_dumps,
    dummy_date_range_dumps,
)


class TestDateRangeSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateRangeSchema(), *dummy_date_range_dumps)


class TestDateSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateSchema(), *date_dumps)


class TestResolvableDateSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateExpressionSchema(), *dummy_date_expression_dumps)
