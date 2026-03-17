from typing import TYPE_CHECKING, Any

from betty.test_utils.jinja import assert_template_string

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestUnique:
    async def test___call__(self) -> None:
        data: Sequence[Any] = [
            999,
            {},
            999,
            {},
        ]
        async with assert_template_string(
            template='{{ data | unique | join(", ") }}',
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == "999, {}"
