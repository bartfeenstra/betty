from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.test_utils.entity.associations.has_file_references import (
    DummyHasFileReferences,
)

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


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
        self, assert_jinja_str: AssertJinja, expected: str, data: Any
    ) -> None:
        template = "{% if data is has_file_references %}true{% else %}false{% endif %}"
        async with assert_jinja_str(template, data={"data": data}) as rendered:
            assert rendered == expected
