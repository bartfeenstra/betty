from __future__ import annotations

import pytest

from betty.jinja2.globals import HtmlId
from betty.test_utils.jinja2 import assert_template_string


class TestHtmlId:
    def test_increment(self) -> None:
        sut = HtmlId()
        assert str(sut) == "0"
        sut.increment()
        assert str(sut) == "1"

    def test___str__(self) -> None:
        sut = HtmlId()
        assert str(sut) == "0"


@pytest.mark.parametrize(
    ("expected", "template"),
    [
        (
            "betty-generated--1",
            "{{ generate_html_id() }}",
        ),
        (
            "betty-generated--1betty-generated--2",
            "{{ generate_html_id() }}{{ generate_html_id() }}",
        ),
    ],
)
async def test_generate_html_id(expected: str, template: str) -> None:
    async with assert_template_string(template=template) as (actual, _):
        assert actual == expected
