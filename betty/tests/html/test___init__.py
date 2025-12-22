from __future__ import annotations

import pytest

from betty.html import (
    NavigationLink,
    NavigationLinkProvider,
    generate_html_id,
    newlines_to_paragraphs,
    plain_text_to_html,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER


class TestNavigationLink:
    def test_url(self) -> None:
        url = "https://example.com"
        sut = NavigationLink(url, "Hello, world!")
        assert sut.url.localize(DEFAULT_LOCALIZER) == url

    def test_label(self) -> None:
        label = Plain("Hello, world!")
        sut = NavigationLink("https://example.com", label)
        assert sut.label is label


class TestNavigationLinkProvider:
    def test_primary_navigation_links(self) -> None:
        sut = NavigationLinkProvider()
        sut.primary_navigation_links()

    def test_secondary_navigation_links(self) -> None:
        sut = NavigationLinkProvider()
        sut.secondary_navigation_links()


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
