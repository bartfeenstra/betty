from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.place import Place
from betty.locale.localize import default_localizer
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = Place()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={raspberry_mint},
        template="search/result--place.html.j2",
    ) as (actual, _):
        assert entity.label.localize(default_localizer) in actual
        assert entity.public_id in actual
