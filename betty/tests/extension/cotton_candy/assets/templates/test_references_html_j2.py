from betty.extension.cotton_candy import CottonCandy
from betty.jinja2 import _Citer
from betty.locale.localizable import plain
from betty.model.ancestry import Citation
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = "references.html.j2"

    async def test_without_references(self) -> None:
        citer = _Citer()
        async with self._render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_public_citation(self) -> None:
        citation = Citation(
            id="C1",
            location=plain("On the shelf over there"),
            public=True,
        )
        citer = _Citer()
        citer.cite(citation)
        async with self._render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as (actual, _):
            assert 'href="/citation/C1/index.html"' in actual

    async def test_with_private_citation(self) -> None:
        citation = Citation(
            id="C1",
            location=plain("On the shelf over there"),
            private=True,
        )
        citer = _Citer()
        citer.cite(citation)
        async with self._render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as (actual, _):
            assert (
                "This citation's details are unavailable to protect people's privacy."
                in actual
            )
