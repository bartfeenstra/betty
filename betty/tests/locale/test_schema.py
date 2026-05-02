from __future__ import annotations

from typing import override

import pytest

from betty.locale.schema import LocaleSchema
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut


class TestLocaleSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut_data(self) -> SchemaTestBaseSut:
        return (
            LocaleSchema(),
            ["en", "nl", "uk"],
            [
                True,
                False,
            ],
        )
