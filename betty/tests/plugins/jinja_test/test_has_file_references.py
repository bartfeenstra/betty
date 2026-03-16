from __future__ import annotations

from typing import Any

import pytest

from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.jinja import assert_template_string


class TestHasFileReferences:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DummyHasFileReferences()),
            ("false", DummyHasFileReferences),
            ("false", object()),
        ],
    )
    async def test___call__(self, expected: str, data: Any) -> None:
        template = "{% if data is has_file_references %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
