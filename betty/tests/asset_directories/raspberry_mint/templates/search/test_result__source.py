from betty.asset_directories import raspberry_mint
from betty.entities.source import Source
from betty.localizer import default_localizer
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = Source()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={raspberry_mint},
        template="search/result--source.html.j2",
    ) as (actual, _):
        assert default_localizer.localize(entity.label) in actual
        assert entity.id in actual
