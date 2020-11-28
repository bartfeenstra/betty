from betty.ancestry import PersonName, Citation, Source
from betty.asyncio import sync
from betty.tests import TemplateTestCase


class TestNameLabel(TemplateTestCase):
    template_string = '{% import \'macro/person.html.j2\' as personMacros %}{{ personMacros.name_label(name, embedded=embedded if embedded is defined else False) }}'

    @sync
    async def test_with_full_name(self):
        name = PersonName('Jane', 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_individual_name(self):
        name = PersonName('Jane')
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_affiliation_name(self):
        name = PersonName(None, 'Dough')
        expected = '<span class="person-label" typeof="foaf:Person">… <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        name = PersonName('Jane', 'Dough')
        source = Source()
        citation = Citation(source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span>'
        async with self._render(data={
            'name': name,
            'embedded': True,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_citation(self):
        name = PersonName('Jane')
        source = Source()
        citation = Citation(source)
        name.citations.append(citation)
        expected = '<span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span></span><a href="#reference-1" class="citation">[1]</a>'
        async with self._render(data={
            'name': name,
        }) as (actual, _):
            self.assertEqual(expected, actual)
