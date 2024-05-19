import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.jinja2 import _Citer
from betty.locale import Str
from betty.model.ancestry import Citation
from betty.tests import TemplateTester


class Test:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(new_temporary_app, template_file="references.html.j2")

    async def test_without_references(self, template_tester: TemplateTester) -> None:
        citer = _Citer()
        async with template_tester.render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as actual:
            assert actual == ""

    async def test_with_public_citation(self, template_tester: TemplateTester) -> None:
        citation = Citation(
            id="C1",
            location=Str.plain("On the shelf over there"),
            public=True,
        )
        citer = _Citer()
        citer.cite(citation)
        async with template_tester.render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as actual:
            assert 'href="/citation/C1/index.html"' in actual

    async def test_with_private_citation(self, template_tester: TemplateTester) -> None:
        citation = Citation(
            id="C1",
            location=Str.plain("On the shelf over there"),
            private=True,
        )
        citer = _Citer()
        citer.cite(citation)
        async with template_tester.render(
            data={
                "citer": citer,
                "page_resource": "/",
            }
        ) as actual:
            assert (
                "This citation's details are unavailable to protect people's privacy."
                in actual
            )
