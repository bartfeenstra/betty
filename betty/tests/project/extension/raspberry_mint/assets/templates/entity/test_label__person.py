from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label--person.html.j2"

    async def test_minimal(self) -> None:
        person = Person()
        expected = '<span title="This person\'s name is unknown.">n.n.</span>'
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_name(self) -> None:
        person = Person()
        PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
        )
        expected = "Jane Dough"
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_persistent_id(self) -> None:
        person = Person(id="P0")
        expected = '<a href="/person/P0/index.html"><span title="This person\'s name is unknown.">n.n.</span></a>'
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_embedded(self) -> None:
        person = Person(id="P0")
        expected = '<span title="This person\'s name is unknown.">n.n.</span>'
        async with self.assert_template_file(
            data={
                "entity": person,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_private(self) -> None:
        person = Person(id="P0", private=True)
        PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
        )
        expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_private_name(self) -> None:
        person = Person()
        PersonName(
            person=person,
            individual="Jane",
            affiliation="Dough",
            private=True,
        )
        expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
        async with self.assert_template_file(
            data={
                "entity": person,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_person_is_context(self) -> None:
        person = Person(id="P0")
        expected = '<span title="This person\'s name is unknown.">n.n.</span>'
        async with self.assert_template_file(
            data={
                "entity": person,
                "entity_contexts": await EntityContexts.new(person),
            }
        ) as (actual, _):
            assert actual == expected
