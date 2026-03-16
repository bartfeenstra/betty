from typing import Any

import pytest

from betty.privacy import Privacy
from betty.test_utils.jinja import assert_template_string
from betty.test_utils.privacy import DummyHasPrivacy


class TestPublic:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("false", DummyHasPrivacy(privacy=Privacy.PRIVATE)),
            ("true", DummyHasPrivacy(privacy=Privacy.PUBLIC)),
            ("true", DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
            ("true", object()),
        ],
    )
    async def test___call__(self, expected: bool, data: Any) -> None:
        template = "{% if data is public %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
