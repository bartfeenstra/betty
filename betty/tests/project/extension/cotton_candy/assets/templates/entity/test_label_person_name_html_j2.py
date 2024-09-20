from betty.ancestry.citation import Citation
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.source import Source
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.assets.templates import TemplateTestBase


class Test(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/label--person-name.html.j2"

    async def test_with_full_name(self) -> None:
        person = Person()
        person_name = PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
        )
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        async with self._render(
            data={
                "person_name": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_individual_name(self) -> None:
        person = Person()
        person_name = PersonName(
            person=person,
            individual="Jane",
        )
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
        async with self._render(
            data={
                "person_name": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_affiliation_name(self) -> None:
        person = Person()
        person_name = PersonName(
            person=person,
            affiliation="Dough",
        )
        expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
        async with self._render(
            data={
                "person_name": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
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
        async with self._render(
            data={
                "person_name": person_name,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_citation(self) -> None:
        person = Person()
        person_name = PersonName(
            person=person,
            individual="Jane",
        )
        source = Source()
        citation = Citation(source=source)
        person_name.citations.add(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
        async with self._render(
            data={
                "person_name": person_name,
            }
        ) as (actual, _):
            assert actual == expected
