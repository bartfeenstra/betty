from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.html import (
    Breadcrumb,
    Breadcrumbs,
    Citer,
    NavigationLink,
    NavigationLinkProvider,
    newlines_to_paragraphs,
)
from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project

if TYPE_CHECKING:
    from betty.app import App


class TestNavigationLink:
    def test_url(self) -> None:
        url = "https://example.com"
        sut = NavigationLink(url, Plain("Hello, world!"))
        assert sut.url.localize(DEFAULT_LOCALIZER) == url

    def test_label(self) -> None:
        label = Plain("Hello, world!")
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


class TestBreadcrumb:
    def test_label(self) -> None:
        label = "My First Page"
        sut = Breadcrumb(label, "betty:///my-first-page")
        assert sut.label == label

    def test_resource(self) -> None:
        resource = "betty:///my-first-page"
        sut = Breadcrumb("My First Page", resource)
        assert sut.resource == resource

    async def test_dump_linked_data__with_items(self, temporary_app: App) -> None:
        sut = Breadcrumb("My First Page", "betty:///my-first-page")
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {
                "@type": "ListItem",
                "item": "https://example.com/my-first-page",
                "name": "My First Page",
            }


class TestBreadcrumbs:
    def test_append(self) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "betty:///my-first-page")

    def test___iter__(self) -> None:
        label = "My First Page"
        resource = "betty:///my-first-page"
        sut = Breadcrumbs()
        sut.append(label, resource)
        actual = list(iter(sut))
        assert actual[0].label == label

    def test___len__(self) -> None:
        label = "My First Page"
        resource = "betty:///my-first-page"
        sut = Breadcrumbs()
        sut.append(label, resource)
        assert len(sut) == 1

    async def test_dump_linked_data__without_items(self, temporary_app: App) -> None:
        sut = Breadcrumbs()
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {}

    async def test_dump_linked_data__with_items(self, temporary_app: App) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "betty:///my-first-page")
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "item": "https://example.com/my-first-page",
                        "name": "My First Page",
                        "position": 1,
                    }
                ],
            }


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
