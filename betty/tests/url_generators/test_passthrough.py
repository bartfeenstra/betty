from __future__ import annotations

from typing import Any

import pytest

from betty.media_types.html import HTML
from betty.url_generators.passthrough import PassthroughUrlGenerator


class TestPassthroughUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "wwwexamplecom"),
            (False, "www.example.com"),
            (False, "http://["),
            (True, "http://www.example.com"),
            (True, "https://www.example.com"),
            (True, "some-scheme://www.example.com"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        sut = PassthroughUrlGenerator()
        assert sut.supports(resource) == expected

    async def test_generate(self) -> None:
        resource = "some-scheme://www.example.com"
        sut = PassthroughUrlGenerator()
        assert sut.generate(resource, media_type=HTML) == resource
