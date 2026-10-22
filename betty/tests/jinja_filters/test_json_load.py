from betty.test_utils.conftest import AssertJinja


class TestJsonLoad:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        data = "[1, 2, 3]"
        template = "{{ data | json_load | json_dump }}"
        async with assert_jinja_str(template, data={"data": data}) as rendered:
            assert rendered == data
