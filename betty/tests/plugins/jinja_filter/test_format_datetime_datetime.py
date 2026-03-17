import datetime

from betty.test_utils.conftest import AssertTemplateString


class TestFormatDatetimeDatetime:
    async def test___call__(self, assert_template_string: AssertTemplateString) -> None:
        template = "{{ data | format_datetime_datetime }}"
        async with assert_template_string(
            template=template,
            data={
                "data": datetime.datetime(1970, 1, 1),
            },
        ) as (actual, _):
            assert actual == "January 1, 1970"
