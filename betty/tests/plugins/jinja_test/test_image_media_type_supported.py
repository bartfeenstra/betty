from __future__ import annotations

from typing import Any

import pytest

from betty.media_type import MediaType
from betty.media_type.media_types import PDF, SVG
from betty.test_utils.jinja import assert_template_string


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
    async def test___call__(self, expected: str, data: Any) -> None:
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
