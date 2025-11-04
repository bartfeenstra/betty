import pytest

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.assertion import assert_static_translations


@pytest.mark.parametrize(
    "value",
    [
        "Hello, world!",
        {
            "en-US": "Hello, world!",
            "nl-NL": "Hallo, wereld!",
            "unknown-locale": "H3ll0, w0rld!",
        },
    ],
)
async def test_assert_static_translations__with_valid_value(
    value: ShorthandStaticTranslations,
) -> None:
    assert_static_translations()(value)


@pytest.mark.parametrize(
    "value",
    [
        True,
        None,
        object(),
        [],
        {
            DEFAULT_LOCALE: 456,
        },
        {
            123: "a valid translation",
        },
        {
            "": "a valid translation",
        },
    ],
)
async def test_assert_static_translations__with_invalid_value(
    value: ShorthandStaticTranslations,
) -> None:
    with pytest.raises(HumanFacingException):
        assert_static_translations()(value)
