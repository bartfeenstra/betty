from __future__ import annotations

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.html import Breadcrumbs, Citer, NavigationLink, NavigationLinkProvider
from betty.locale.localizable import plain
from betty.locale.localizer import DEFAULT_LOCALIZER


class TestNavigationLink:
    def test_url(self) -> None:
        url = "https://example.com"
        sut = NavigationLink(url, plain("Hello, world!"))
        assert sut.url.localize(DEFAULT_LOCALIZER) == url

    def test_label(self) -> None:
        label = plain("Hello, world!")
        sut = NavigationLink("https://example.com", label)
        assert sut.label == label


class TestNavigationLinkProvider:
    def test_primary_navigation_links(self) -> None:
        sut = NavigationLinkProvider()
        sut.primary_navigation_links()

    def test_secondary_navigation_links(self) -> None:
        sut = NavigationLinkProvider()
        sut.secondary_navigation_links()


class TestCiter:
    def test_cite(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        assert sut.cite(citation1) == 1
        assert sut.cite(citation2) == 2
        assert sut.cite(citation1) == 1

    def test___iter__(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert list(sut) == [(1, citation1), (2, citation2)]

    def test___len__(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert len(sut) == 2


class TestBreadcrumbs:
    def test_append(self) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "/my-first-page")

    def test_dump__without_items(self) -> None:
        sut = Breadcrumbs()
        assert sut.dump() == {}

    def test_dump__with_items(self) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "/my-first-page")
        assert sut.dump() == {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "item": "/my-first-page",
                    "name": "My First Page",
                    "position": 1,
                }
            ],
        }
