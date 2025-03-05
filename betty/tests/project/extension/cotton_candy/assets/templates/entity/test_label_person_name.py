from betty.ancestry.citation import Citation
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.source import Source
from betty.project.extension.cotton_candy import CottonCandy

from betty.test_utils.jinja2 import assert_template_file


async def test_with_full_name() -> None:
    person = Person()
    person_name = PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
    async with assert_template_file(
        data={
            "person_name": person_name,
        },
        extensions={CottonCandy},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_individual_name() -> None:
    person = Person()
    person_name = PersonName(
        person=person,
        individual="Jane",
    )
    expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
    async with assert_template_file(
        data={
            "person_name": person_name,
        },
        extensions={CottonCandy},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_affiliation_name() -> None:
    person = Person()
    person_name = PersonName(
        person=person,
        affiliation="Dough",
    )
    expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
    async with assert_template_file(
        data={
            "person_name": person_name,
        },
        extensions={CottonCandy},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    person = Person()
    person_name = PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    source = Source()
    citation = Citation(source=source)
    person_name.citations.add(citation)
    expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
    async with assert_template_file(
        data={
            "person_name": person_name,
            "embedded": True,
        },
        extensions={CottonCandy},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citation() -> None:
    person = Person()
    person_name = PersonName(
        person=person,
        individual="Jane",
    )
    source = Source()
    citation = Citation(source=source)
    person_name.citations.add(citation)
    expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
    async with assert_template_file(
        data={
            "person_name": person_name,
        },
        extensions={CottonCandy},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected
