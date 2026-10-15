from betty.localizables.plain import Plain
from betty.test_utils.conftest import AssertJinja


class TestLocalize:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        template = "{{ data | localize }}"
        async with assert_jinja_str(
            template, data={"data": Plain("Hello, world!")}
        ) as rendered:
            assert rendered == "Hello, world!"
