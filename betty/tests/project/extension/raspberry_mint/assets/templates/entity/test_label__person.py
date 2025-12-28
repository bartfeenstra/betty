from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.document import Document, EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    person = Person()
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_name() -> None:
    person = Person()
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = "Jane Dough"
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id() -> None:
    person = Person(id="P0")
    expected = f'<a href="/person/{person.public_id}/index.html"><span title="This person\'s name is unknown.">n.n.</span></a>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    person = Person(id="P0")
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": person,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_private() -> None:
    person = Person(id="P0", private=True)
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_private_name() -> None:
    person = Person()
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
        private=True,
    )
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_person_is_context() -> None:
    person = Person(id="P0")
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": person,
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        extensions={RaspberryMint},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected
