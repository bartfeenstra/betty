"""
Provide the HTML API, for generating HTML pages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import Lock
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.link import Link
from betty.serde.dump import Dump, Dumpable, DumpMapping

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence

    from betty.ancestry.citation import Citation
    from betty.locale.localizable import (
        Localizable,
    )


class CssProvider(ABC):
    """
    Provide CSS for HTML pages.
    """

    @property
    @abstractmethod
    def public_css_paths(self) -> Sequence[str]:
        """
        The public URL paths to the CSS files to include in each HTML page.
        """


class JsProvider(ABC):
    """
    Provide JavaScript for HTML pages.
    """

    @property
    @abstractmethod
    def public_js_paths(self) -> Sequence[str]:
        """
        The public URL paths to the JavaScript files to include in each HTML page.
        """


@final
class NavigationLink(Link):
    """
    A navigation link.
    """

    def __init__(self, url: str, label: Localizable):
        self._url = url
        self._label = label

    @override
    @property
    def url(self) -> str:
        return self._url

    @override
    @property
    def label(self) -> Localizable:
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


class Citer:
    """
    Track citations when they are first used.
    """

    __slots__ = "_lock", "_cited"

    def __init__(self):
        self._lock = Lock()
        self._cited: MutableSequence[Citation] = []

    def __iter__(self) -> enumerate[Citation]:
        return enumerate(self._cited, 1)

    def __len__(self) -> int:
        return len(self._cited)

    def cite(self, citation: Citation) -> int:
        """
        Reference a citation.

        :returns: The citation's sequential reference number.
        """
        with self._lock:
            if citation not in self._cited:
                self._cited.append(citation)
            return self._cited.index(citation) + 1


class _Breadcrumb(Dumpable):
    def __init__(self, label: str, url: str):
        self._label = label
        self._url = url

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "@type": "ListItem",
            "name": self._label,
            "item": self._url,
        }


class Breadcrumbs(Dumpable):
    """
    A trail of navigational breadcrumbs.
    """

    def __init__(self):
        self._breadcrumbs: MutableSequence[_Breadcrumb] = []

    def append(self, label: str, url: str) -> None:
        """
        Append a breadcrumb to the trail.
        """
        self._breadcrumbs.append(_Breadcrumb(label, url))

    @override
    def dump(self) -> Dump:
        if not self._breadcrumbs:
            return {}
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "position": position,
                    **breadcrumb.dump(),
                }
                for position, breadcrumb in enumerate(self._breadcrumbs, 1)
            ],
        }
