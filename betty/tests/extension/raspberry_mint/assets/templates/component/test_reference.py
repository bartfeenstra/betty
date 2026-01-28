from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "citations": [],
        },
        extensions={RaspberryMint},
        template="component/reference.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_citation() -> None:
    async with assert_template_file(
        data={
            "citations": [
                Citation(source=Source()),
            ],
        },
        extensions={RaspberryMint},
        template="component/reference.html.j2",
    ) as (actual, _):
        assert actual == ' <sup><a href="#reference-1">[1]</a></sup>'
