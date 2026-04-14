from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.media_type import MediaType
from betty.media_type.media_types import PDF, SVG

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateString


class TestImageMediaTypeSupported:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", PDF),
            ("true", SVG),
            ("true", MediaType("image/gif")),
            ("true", MediaType("image/jpeg")),
            ("true", MediaType("image/png")),
            ("false", MediaType("text/plain")),
            ("false", MediaType("application/json")),
            ("false", None),
        ],
    )
    async def test___call__(
        self, assert_template_string: AssertTemplateString, expected: str, data: Any
    ) -> None:
        template = (
            "{% if data is image_media_type_supported %}true{% else %}false{% endif %}"
        )
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
