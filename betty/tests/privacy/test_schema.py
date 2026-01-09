from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from typing_extensions import override

from betty.privacy.schema import PrivacySchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut

if TYPE_CHECKING:
    from collections.abc import Iterable


class TestPrivacySchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        return [
            (PrivacySchema(), [True, False], [None, 123, "abc", [], {}]),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut_data(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)
