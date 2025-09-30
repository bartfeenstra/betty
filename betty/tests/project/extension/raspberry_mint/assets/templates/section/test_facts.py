from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file
from betty.test_utils.model import DummyEntityOne


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "facts": [],
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/facts.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_fact() -> None:
    fact = DummyEntityOne()
    async with assert_template_file(
        data={
            "facts": [fact],
            "page_resource": "betty:///index.html",
        },
        extensions={RaspberryMint},
        template="section/facts.html.j2",
    ) as (actual, _):
        assert fact.label.localize(DEFAULT_LOCALIZER) in actual
