from typing import TYPE_CHECKING, Any

from betty.test_utils.conftest import AssertJinja

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestUnique:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        data: Sequence[Any] = [999, {}, 999, {}]
        async with assert_jinja_str(
            '{{ data | unique | join(", ") }}', data={"data": data}
        ) as rendered:
            assert rendered == "999, {}"
