from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.entity.event import Event
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    event = Event()
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={RASPBERRY_MINT},
        template="entity/summary--event.html.j2",
    ) as (actual, _):
        assert actual
