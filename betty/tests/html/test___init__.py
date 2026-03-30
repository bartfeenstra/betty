from __future__ import annotations

import pytest

from betty.html import generate_html_id, newlines_to_paragraphs, plain_text_to_html


@pytest.mark.parametrize(
    ("expected", "text"),
    [
        ("<p></p>", ""),
        (
            "<p>Apples <br>\n and <br>\n oranges</p>",
            "Apples \n and \n oranges",
        ),
    ],
)
def test_newlines_to_paragraphs(expected: str, text: str) -> None:
    assert newlines_to_paragraphs(text) == expected


def test_generate_html_id() -> None:
    assert generate_html_id()
    assert generate_html_id() != generate_html_id()


def test_plain_text_to_html() -> None:
    assert (
        plain_text_to_html("Hello...\n~!@#$%^&*()_+\n...world!")
        == "<p>Hello...<br>\n~!@#$%^&amp;*()_+<br>\n...world!</p>"
    )
