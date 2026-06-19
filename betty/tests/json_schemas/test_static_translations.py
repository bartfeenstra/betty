from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, cast, override

import pytest

from betty.json_schemas.static_translations import StaticTranslationsSchema
from betty.locale import default_locale_tag
from betty.test_utils.json_schema import SchemaTestBase, SchemaTestBaseSut

if TYPE_CHECKING:
    from betty.portable import PortableData


class TestStaticTranslationsSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        valid_datas: Sequence[PortableData] = [
            {default_locale_tag: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ]
        invalid_datas: Sequence[PortableData] = [
            True,
            False,
            None,
            123,
            [],
            {default_locale_tag: True},
            {default_locale_tag: False},
            {default_locale_tag: None},
            {default_locale_tag: 123},
            {default_locale_tag: []},
            {default_locale_tag: {}},
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
