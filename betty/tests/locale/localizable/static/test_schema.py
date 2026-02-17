from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, cast, override

import pytest

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut

if TYPE_CHECKING:
    from betty.portable import PortableData


class TestStaticTranslationsSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        valid_datas: Sequence[PortableData] = [
            {DEFAULT_LOCALE_TAG: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ]
        invalid_datas: Sequence[PortableData] = [
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
    def sut_data(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)
