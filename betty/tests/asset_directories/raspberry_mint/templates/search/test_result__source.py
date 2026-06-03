from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.entities.source import Source
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = Source()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={RASPBERRY_MINT},
        template="search/result--source.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
