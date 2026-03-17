from betty.test_utils.jinja import assert_template_string


class TestJsonLoad:
    async def test___call__(self) -> None:
        data = "[1, 2, 3]"
        template = "{{ data | json_load | json_dump }}"
        async with assert_template_string(
            template=template,
            data={"data": data},
        ) as (actual, _):
            assert actual == data
