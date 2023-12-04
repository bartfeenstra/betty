from betty.extension import CottonCandy
from betty.model.ancestry import PersonName, Citation, Source, Person
from betty.tests import TemplateTestCase


class TestNameLabel(TemplateTestCase):
    extensions = {CottonCandy}
    template_string = '{% import \'macro/person.html.j2\' as personMacros %}{{ personMacros.name_label(name, embedded=embedded if embedded is defined else False) }}'

    async def test_with_full_name(self) -> None:
        person = Person()
        name = PersonName(
            person=person,
            individual='Jane',
            affiliation='Dough',
        )
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    async def test_with_individual_name(self) -> None:
        person = Person()
        name = PersonName(
            person=person,
            individual='Jane',
        )
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    async def test_with_affiliation_name(self) -> None:
        person = Person()
        name = PersonName(
            person=person,
            affiliation='Dough',
        )
        expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual

    async def test_embedded(self) -> None:
        person = Person()
        name = PersonName(
            person=person,
            individual='Jane',
            affiliation='Dough',
        )
        source = Source()
        citation = Citation(source=source)
        name.citations.add(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual

    async def test_with_citation(self) -> None:
        person = Person()
        name = PersonName(
            person=person,
            individual='Jane',
        )
        source = Source()
        citation = Citation(source=source)
        name.citations.add(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            assert expected == actual
