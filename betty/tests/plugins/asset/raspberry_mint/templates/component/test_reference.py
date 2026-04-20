from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "citations": [],
        },
        assets={RASPBERRY_MINT},
        template="component/reference.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_citation(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "citations": [
                Citation(source=Source()),
            ],
        },
        assets={RASPBERRY_MINT},
        template="component/reference.html.j2",
    ) as (actual, _):
        assert actual == ' <sup><a href="#reference-1">[1]</a></sup>'
