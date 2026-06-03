from betty.test_utils.conftest import AssertTemplateString


class TestJsonDump:
    async def test___call__(self, assert_template_string: AssertTemplateString) -> None:
        template = "{{ data | json_dump }}"
        async with assert_template_string(
            template=template,
            data={"data": [1, 2, 3]},
        ) as (actual, _):
            assert actual == "[1, 2, 3]"
