from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.html import Citer
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_without_references() -> None:
    citer = Citer()
    async with assert_template_file(
        data={
            "citer": citer,
            "page_resource": "betty:///",
        },
        extensions={CottonCandy},
        template="references.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_public_citation() -> None:
    citation = Citation(
        source=Source(),
        id="C1",
        location="On the shelf over there",
        public=True,
    )
    citer = Citer()
    citer.cite(citation)
    async with assert_template_file(
        data={
            "citer": citer,
            "page_resource": "betty:///",
        },
        extensions={CottonCandy},
        template="references.html.j2",
    ) as (actual, _):
        assert 'href="/citation/C1/index.html"' in actual


async def test_with_private_citation() -> None:
    citation = Citation(
        source=Source(),
        id="C1",
        location="On the shelf over there",
        private=True,
    )
    citer = Citer()
    citer.cite(citation)
    async with assert_template_file(
        data={
            "citer": citer,
            "page_resource": "betty:///",
        },
        extensions={CottonCandy},
        template="references.html.j2",
    ) as (actual, _):
        assert (
            "This citation's details are unavailable to protect people's privacy."
            in actual
        )
