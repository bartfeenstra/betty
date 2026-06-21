from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.person import Person
from betty.localizer import default_localizer
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    entity = Person()
    async with assert_template_file(
        data={
            "entity": entity,
        },
        assets={raspberry_mint},
        template="search/result.html.j2",
    ) as (actual, _):
        assert entity.label.localize(default_localizer) in actual
        assert entity.id in actual
