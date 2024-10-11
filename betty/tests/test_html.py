from __future__ import annotations

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.html import Citer, Breadcrumbs
from betty.test_utils.assets.templates import TemplateTestBase


class TestCiter(TemplateTestBase):
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

    def test_dump_without_items(self) -> None:
        sut = Breadcrumbs()
        assert sut.dump() == {}

    def test_dump_with_items(self) -> None:
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
