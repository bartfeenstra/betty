from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    source = Source()
    citation = Citation(source=source)
    async with assert_template_file(
        data={
            "entity": citation,
        },
        assets={RASPBERRY_MINT},
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
        assets={RASPBERRY_MINT},
        template="entity/summary--citation.html.j2",
    ) as (actual, _):
        assert source.id not in actual
