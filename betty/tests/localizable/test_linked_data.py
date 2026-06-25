import pytest

from betty.json_schemas.static_translations import new_static_translations_schema
from betty.localizable import ShorthandStaticTranslations
from betty.localizable.linked_data import dump_linked_data
from betty.localizables.static import StaticTranslations
from betty.localizer import default_localizer
from betty.portable import PortableMapping
from betty.test_utils.linked_data import validate


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
    expected: PortableMapping, translations: ShorthandStaticTranslations
) -> None:
    data = dump_linked_data(
        StaticTranslations(translations), localizers=[default_localizer]
    )
    validate(new_static_translations_schema(), data)
    assert data == expected
