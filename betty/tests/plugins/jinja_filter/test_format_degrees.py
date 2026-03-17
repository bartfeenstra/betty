import pytest

from betty.test_utils.conftest import AssertTemplateString


class TestFormatDegrees:
    @pytest.mark.parametrize(
        ("expected", "template"),
        [
            ("0° 0&#39; 0&#34;", "{{ 0 | format_degrees }}"),
            ("52° 22&#39; 1&#34;", "{{ 52.367 | format_degrees }}"),
        ],
    )
    async def test___call__(
        self, assert_template_string: AssertTemplateString, expected: str, template: str
    ) -> None:
        async with assert_template_string(template=template) as (actual, _):
            assert actual == expected
