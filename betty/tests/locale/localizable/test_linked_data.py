import pytest

from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.serde.dump import Dump, DumpMapping
from betty.test_utils.json.linked_data import assert_linked_data_dump


@pytest.mark.parametrize(
    ("expected", "translations"),
    [
        (
            {"en-US": "Hello, world!"},
            {
                "en-US": "Hello, world!",
            },
        ),
        (
            {"nl-NL": "Hallo, wereld!", "en": "Hello, world!"},
            {
                "nl-NL": "Hallo, wereld!",
                "en": "Hello, world!",
            },
        ),
    ],
)
async def test_dump_linked_data(
    expected: DumpMapping[Dump], translations: ShorthandStaticTranslations
) -> None:
    actual = await assert_linked_data_dump(
        StaticTranslationsSchema(),
        dump_linked_data(
            StaticTranslations(translations), localizers=[DEFAULT_LOCALIZER]
        ),
    )
    assert actual == expected
