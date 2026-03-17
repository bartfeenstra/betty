import pytest
from babel import Locale

from betty.test_utils.jinja import assert_template_string


class TestToLanguageTag:
    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("und", None),
            ("nl", Locale("nl")),
            ("nl-NL", Locale("nl", "NL")),
        ],
    )
    async def test___call__(self, expected: str, locale: Locale | None) -> None:
        template = "{{ data | to_language_tag }}"
        async with assert_template_string(
            template=template,
            data={"data": locale},
        ) as (actual, _):
            assert actual == expected
