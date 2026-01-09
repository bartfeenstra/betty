from __future__ import annotations

import pytest
from typing_extensions import override

from betty.date.schema import DateLikeSchema, DateRangeSchema, DateSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut
from betty.tests.date.test___init__ import (
    _DUMMY_DATE_DUMPS,
    _DUMMY_DATE_LIKE_DUMPS,
    _DUMMY_DATE_RANGE_DUMPS,
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


class TestDateLikeSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (DateLikeSchema(), *_DUMMY_DATE_LIKE_DUMPS)
