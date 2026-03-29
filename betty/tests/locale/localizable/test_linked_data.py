import pytest

from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.portable import PortableMapping
from betty.test_utils.conftest import AssertLinkedDataDump


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
    assert_linked_data_dump: AssertLinkedDataDump,
    expected: PortableMapping,
    translations: ShorthandStaticTranslations,
) -> None:
    actual = await assert_linked_data_dump(
        StaticTranslationsSchema(),
        dump_linked_data(
            StaticTranslations(translations), localizers=[DEFAULT_LOCALIZER]
        ),
    )
    assert actual == expected
