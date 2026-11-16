from betty.entities.event import Event
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    event = Event()
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--event.html.j2", data={"entity": event}
    ) as rendered:
        assert rendered
