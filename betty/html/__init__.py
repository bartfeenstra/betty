"""
Provide the HTML API, for generating HTML pages.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final
from uuid import uuid4

from markupsafe import escape

from betty.locale.localizable import resolve_localizable

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.locale.localizable import Localizable, ResolvableLocalizable


class CssProvider(ABC):
    """
    Provide CSS for HTML pages.
    """

    @abstractmethod
    async def get_public_css_paths(self) -> Sequence[str]:
        """
        The URL-generatable resources of the CSS files to include in each HTML page.
        """


@final
class NavigationLink:
    """
    A navigation link.
    """

    def __init__(self, url: ResolvableLocalizable, label: ResolvableLocalizable):
        self._url = resolve_localizable(url)
        self._label = resolve_localizable(label)

    @property
    def url(self) -> Localizable:
        """
        The URL the link points to.
        """
        return self._url

    @property
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """
        return self._label


class NavigationLinkProvider:
    """
    Provide navigation links for HTML pages.
    """

    def primary_navigation_links(self) -> Sequence[NavigationLink]:
        """
        The primary navigation links.
        """
        return ()

    def secondary_navigation_links(self) -> Sequence[NavigationLink]:
        """
        The secondary navigation links.
        """
        return ()


_paragraph_re = re.compile(r"(?:\r\n|\r|\n){2,}")


def newlines_to_paragraphs(text: str) -> str:
    """
    Convert newlines to <p> and <br> tags.
    """
    return "\n\n".join(
        "<p>{}</p>".format(paragraph.replace("\n", "<br>\n"))
        for paragraph in _paragraph_re.split(text)
    )


def plain_text_to_html(text: str) -> str:
    """
    Convert plain text to HTML.
    """
    return newlines_to_paragraphs(escape(text))


def generate_html_id() -> str:
    """
    Generate a unique HTML ID.
    """
    return f"betty-generated--{uuid4()}"
