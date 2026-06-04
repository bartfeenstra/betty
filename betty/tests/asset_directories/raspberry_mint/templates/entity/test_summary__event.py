from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.event import Event
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    event = Event()
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={raspberry_mint},
        template="entity/summary--event.html.j2",
    ) as (actual, _):
        assert actual
