from typing import Any

import pytest

from betty.test_utils.conftest import AssertTemplateString
from betty.test_utils.model import DummyEntityOne


class TestUrl:
    @pytest.mark.parametrize(
        ("expected", "data", "absolute"),
        [
            ("/index.html", "betty:///index.html", False),
            ("/index.html", "betty-static:///index.html", False),
            (
                "https://example.com/dummy-one/0e51a87ec173dd9534a056a403c85881/index.html",
                DummyEntityOne("E0"),
                True,
            ),
        ],
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        data: Any,
        absolute: bool,
    ) -> None:
        template = "{{ data | url(absolute=absolute) }}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
                "absolute": absolute,
            },
        ) as (actual, _):
            assert actual == expected
