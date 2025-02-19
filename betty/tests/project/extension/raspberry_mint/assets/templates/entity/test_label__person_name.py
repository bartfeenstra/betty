from betty.ancestry.citation import Citation
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.source import Source
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label--person-name.html.j2"

    async def test_minimal_with_individual_name(self) -> None:
        person = Person()
        person_name = PersonName(person=person, individual="Jane")
        expected = "Jane"
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_minimal_with_affiliation_name(self) -> None:
        person = Person()
        person_name = PersonName(person=person, affiliation="Dough")
        expected = "… Dough"
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_person_with_persistent_id(self) -> None:
        person = Person(id="P0")
        person_name = PersonName(person=person, individual="Jane")
        expected = '<a href="/person/P0/index.html">Jane</a>'
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        source = Source()
        citation = Citation(source=source)
        person = Person(id="P0")
        person_name = PersonName(person=person, individual="Jane", citations=[citation])
        expected = "Jane"
        async with self.assert_template_file(
            data={
                "entity": person_name,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_private(self) -> None:
        person = Person(id="P0")
        person_name = PersonName(person=person, individual="Jane", private=True)
        expected = '<a href="/person/P0/index.html"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></a>'
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_private_person(self) -> None:
        person = Person(id="P0", private=True)
        person_name = PersonName(person=person, individual="Jane")
        expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_person_is_context(self) -> None:
        person = Person(id="P0")
        person_name = PersonName(person=person, individual="Jane")
        expected = "Jane"
        async with self.assert_template_file(
            data={
                "entity": person_name,
                "entity_contexts": await EntityContexts.new(person),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_citations(self) -> None:
        source = Source()
        citation = Citation(source=source)
        person = Person()
        person_name = PersonName(person=person, individual="Jane", citations=[citation])
        expected = 'Jane <sup><a href="#reference-1">[1]</a></sup>'
        async with self.assert_template_file(
            data={
                "entity": person_name,
            }
        ) as (actual, _):
            assert actual == expected
