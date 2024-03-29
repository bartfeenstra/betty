from betty.extension import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Person, Presence, Event, PersonName, Source, Citation, Subject
from betty.model.event_type import Birth, Death
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/meta--person.html.j2'

    async def test_without_meta(self) -> None:
        person = Person(id='P0')
        expected = '<div class="meta person-meta"></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_private(self) -> None:
        person = Person(
            id='P0',
            private=True,
        )
        expected = '<div class="meta person-meta"><p>This person\'s details are unavailable to protect their privacy.</p></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_with_one_alternative_name(self) -> None:
        person = Person(id='P0')
        PersonName(
            person=person,
            individual='Jane',
            affiliation='Dough',
        )
        name = PersonName(
            person=person,
            individual='Janet',
            affiliation='Doughnut',
        )
        name.citations.add(Citation(source=Source(name='The Source')))
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span><a href="#reference-1" class="citation">[1]</a></span></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_with_multiple_alternative_names(self) -> None:
        person = Person(id='P0')
        PersonName(
            person=person,
            individual='Jane',
            affiliation='Dough',
        )
        PersonName(
            person=person,
            individual='Janet',
            affiliation='Doughnut',
        )
        PersonName(
            person=person,
            individual='Janetar',
            affiliation='Of Doughnuton',
        )
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span>, <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janetar</span> <span property="foaf:familyName">Of Doughnuton</span></span></span></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_with_start_of_life_event(self) -> None:
        person = Person(id='P0')
        Presence(person, Subject(), Event(
            event_type=Birth,
            date=Date(1970),
        ))
        expected = '<div class="meta person-meta"><dl><div><dt>Birth</dt><dd>1970</dd></div></dl></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_with_end_of_life_event(self) -> None:
        person = Person(id='P0')
        Presence(person, Subject(), Event(
            event_type=Death,
            date=Date(1970),
        ))
        expected = '<div class="meta person-meta"><dl><div><dt>Death</dt><dd>1970</dd></div></dl></div>'
        async with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    async def test_embedded(self) -> None:
        person = Person(id='P0')
        Presence(person, Subject(), Event(
            event_type=Birth,
            date=Date(1970),
        ))
        PersonName(
            person=person,
            individual='Jane',
            affiliation='Dough',
        )
        name = PersonName(
            person=person,
            individual='Janet',
            affiliation='Doughnut',
        )
        name.citations.add(Citation(source=Source(name='The Source')))
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span></span><dl><div><dt>Birth</dt><dd>1970</dd></div></dl></div>'
        async with self._render(data={
            'entity': person,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual
