from __future__ import annotations

from typing import override

import pytest

from betty.date.schema import DateRangeSchema, DateSchema, ResolvableDateSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut
from betty.tests.date.test___init__ import (
    _DUMMY_DATE_DUMPS,
    _DUMMY_DATE_RANGE_DUMPS,
    _DUMMY_RESOLVABLE_DATE_DUMPS,
)


class TestDateRangeSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateRangeSchema(), *_DUMMY_DATE_RANGE_DUMPS)


class TestDateSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateSchema(), *_DUMMY_DATE_DUMPS)


class TestResolvableDateSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (ResolvableDateSchema(), *_DUMMY_RESOLVABLE_DATE_DUMPS)
