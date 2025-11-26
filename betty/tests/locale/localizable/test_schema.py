from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, cast

import pytest
from typing_extensions import override

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.schema import StaticTranslationsSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestStaticTranslationsSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        valid_datas: Sequence[Dump] = [
            {DEFAULT_LOCALE_TAG: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ]
        invalid_datas: Sequence[Dump] = [
            True,
            False,
            None,
            123,
            [],
            {DEFAULT_LOCALE_TAG: True},
            {DEFAULT_LOCALE_TAG: False},
            {DEFAULT_LOCALE_TAG: None},
            {DEFAULT_LOCALE_TAG: 123},
            {DEFAULT_LOCALE_TAG: []},
            {DEFAULT_LOCALE_TAG: {}},
        ]
        return [
            (
                StaticTranslationsSchema(),
                valid_datas,
                invalid_datas,
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)
