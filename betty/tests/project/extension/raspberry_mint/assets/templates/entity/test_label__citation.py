from __future__ import annotations

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.date import Date
from betty.jinja2 import EntityContexts
from betty.locale.localizable import Plain
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    source = Source()
    citation = Citation(source=source)
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id() -> None:
    source = Source()
    citation = Citation(id="C0", source=source)
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    source = Source()
    citation = Citation(id="C0", source=source)
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
    async with assert_template_file(
        data={
            "entity": citation,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_private_source() -> None:
    source = Source(private=True)
    citation = Citation(source=source)
    expected = '<span class="citation-location"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></span>'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_source_author() -> None:
    source = Source(author=Plain("Bart"))
    citation = Citation(source=source)
    expected = f'Bart. <i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>.'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_source_publisher() -> None:
    source = Source(publisher=Plain("Bart"))
    citation = Citation(source=source)
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Bart.'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_location() -> None:
    source = Source()
    citation = Citation(source=source, location=Plain("Somewhere"))
    expected = (
        f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Somewhere.'
    )
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citation_context() -> None:
    source = Source()
    citation = Citation(id="C0", source=source, location=Plain("Somewhere"))
    expected = (
        f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Somewhere.'
    )
    async with assert_template_file(
        data={
            "entity": citation,
            "entity_contexts": EntityContexts(citation),
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_date() -> None:
    source = Source()
    citation = Citation(source=source, date=Date(1970, 1, 1))
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. Accessed January 1, 1970.'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_private() -> None:
    source = Source()
    citation = Citation(source=source, private=True)
    expected = f'<i>"<span lang="und" dir="auto">Source {source.id}</span>"</i>. <span class="citation-location"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></span>'
    async with assert_template_file(
        data={
            "entity": citation,
        },
        extensions={RaspberryMint},
        template="entity/label--citation.html.j2",
    ) as (actual, _):
        assert actual == expected
