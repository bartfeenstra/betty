import pytest
from babel import Locale

from betty.test_utils.conftest import AssertJinja


class TestToLanguageTag:
    @pytest.mark.parametrize(
        ("expected", "locale"),
        [
            ("und", None),
            ("nl", Locale("nl")),
            ("nl-NL", Locale("nl", "NL")),
        ],
    )
    async def test___call__(
        self,
        assert_jinja_str: AssertJinja,
        expected: str,
        locale: Locale | None,
    ) -> None:
        template = "{{ data | to_language_tag }}"
        async with assert_jinja_str(template, data={"data": locale}) as rendered:
            assert rendered == expected
