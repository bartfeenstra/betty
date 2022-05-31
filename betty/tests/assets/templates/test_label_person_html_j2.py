from betty.model.ancestry import Person, PersonName
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'entity/label--person.html.j2'

    def test_with_name(self):
        person = Person('P0')
        PersonName(person, 'Jane', 'Dough')
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_without_name(self):
        person = Person('P0')
        expected = '<a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_embedded(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        with self._render(data={
            'entity': person,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual

    def test_person_is_context(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        with self._render(data={
            'entity': person,
            'person_context': person,
        }) as (actual, _):
            assert expected == actual

    def test_private(self):
        person = Person('P0')
        person.private = True
        expected = '<a href="/person/P0/index.html"><span class="private" title="This person\'s details are unavailable to protect their privacy.">private</span></a>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_with_entity(self):
        person = Person('P0')
        PersonName(person, 'Jane', 'Dough')
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual
