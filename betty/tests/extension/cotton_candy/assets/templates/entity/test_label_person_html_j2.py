import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.jinja2 import EntityContexts
from betty.model.ancestry import Person, PersonName
from betty.tests import TemplateTester


class Test:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(
            new_temporary_app, template_file="entity/label--person.html.j2"
        )

    async def test_with_name(self, template_tester: TemplateTester) -> None:
        person = Person(id="P0")
        PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
        )
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        async with template_tester.render(
            data={
                "entity": person,
            }
        ) as actual:
            assert expected == actual

    async def test_without_name(self, template_tester: TemplateTester) -> None:
        person = Person(id="P0")
        expected = '<a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with template_tester.render(
            data={
                "entity": person,
            }
        ) as actual:
            assert expected == actual

    async def test_embedded(self, template_tester: TemplateTester) -> None:
        person = Person(id="P0")
        expected = (
            '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        )
        async with template_tester.render(
            data={
                "entity": person,
                "embedded": True,
            }
        ) as actual:
            assert expected == actual

    async def test_person_is_context(self, template_tester: TemplateTester) -> None:
        person = Person(id="P0")
        expected = (
            '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        )
        async with template_tester.render(
            data={
                "entity": person,
                "entity_contexts": EntityContexts(person),
            }
        ) as actual:
            assert expected == actual

    async def test_private(self, template_tester: TemplateTester) -> None:
        person = Person(
            id="P0",
            private=True,
        )
        expected = '<span class="private" title="This person\'s details are unavailable to protect their privacy.">private</span>'
        async with template_tester.render(
            data={
                "entity": person,
            }
        ) as actual:
            assert expected == actual

    async def test_with_entity(self, template_tester: TemplateTester) -> None:
        person = Person(id="P0")
        PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
        )
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        async with template_tester.render(
            data={
                "entity": person,
            }
        ) as actual:
            assert expected == actual
