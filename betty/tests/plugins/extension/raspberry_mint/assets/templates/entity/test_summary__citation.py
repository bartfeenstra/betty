from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(source=source)
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/summary--citation.html.j2",
    ) as (actual, _):
        assert source.public_id in actual


async def test_with_private_source(assert_template_file: AssertTemplateFile) -> None:
    source = Source(privacy=Privacy.PRIVATE)
    citation = Citation(source=source)
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/summary--citation.html.j2",
    ) as (actual, _):
        assert source.id not in actual
