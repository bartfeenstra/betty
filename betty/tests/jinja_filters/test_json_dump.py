from betty.test_utils.conftest import AssertJinja


class TestJsonDump:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        template = "{{ data | json_dump }}"
        async with assert_jinja_str(template, data={"data": [1, 2, 3]}) as rendered:
            assert rendered == "[1, 2, 3]"
