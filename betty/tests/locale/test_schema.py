from __future__ import annotations

import pytest
from typing_extensions import override

from betty.locale.schema import LocaleSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


class TestLocaleSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (
            LocaleSchema(),
            ["en", "nl", "uk"],
            [
                True,
                False,
            ],
        )
