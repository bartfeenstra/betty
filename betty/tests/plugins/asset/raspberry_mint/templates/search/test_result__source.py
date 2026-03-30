from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.asset.raspberry_mint import RaspberryMint
from betty.plugins.entity.source import Source
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = Source()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={RaspberryMint},
        template="search/result--source.html.j2",
    ) as (actual, _):
        assert entity.label.localize(DEFAULT_LOCALIZER) in actual
        assert entity.public_id in actual
