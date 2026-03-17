from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateString


class TestHasFileReferences:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", DummyHasFileReferences()),
            ("false", DummyHasFileReferences),
            ("false", object()),
        ],
    )
    async def test___call__(
        self, assert_template_string: AssertTemplateString, expected: str, data: Any
    ) -> None:  # noqa: F821
        template = "{% if data is has_file_references %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
