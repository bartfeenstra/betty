from betty.locale.localizable.plain import Plain
from betty.test_utils.conftest import AssertTemplateString


class TestLocalize:
    async def test___call__(self, assert_template_string: AssertTemplateString) -> None:
        template = "{{ data | localize }}"
        async with assert_template_string(
            template=template,
            data={"data": Plain("Hello, world!")},
        ) as (actual, _):
            assert actual == "Hello, world!"
