import datetime

from betty.test_utils.conftest import AssertJinja


class TestFormatDatetimeDatetime:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        template = "{{ data | format_datetime_datetime }}"
        async with assert_jinja_str(
            template, data={"data": datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC)}
        ) as rendered:
            assert rendered == "January 1, 1970"
