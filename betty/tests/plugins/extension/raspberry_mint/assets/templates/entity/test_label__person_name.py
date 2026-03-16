from betty.ancestry.citation import Citation
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.source import Source
from betty.document import Document, EntityContexts
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.privacy import Privacy
from betty.test_utils.jinja import assert_template_file


async def test_minimal_with_individual_name() -> None:
    person = Person()
    person_name = PersonName(person=person, individual="Jane")
    expected = "Jane"
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_minimal_with_affiliation_name() -> None:
    person = Person()
    person_name = PersonName(person=person, affiliation="Dough")
    expected = "… Dough"
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_person_with_persistent_id() -> None:
    person = Person(id="P0")
    person_name = PersonName(person=person, individual="Jane")
    expected = f'<a href="/person/{person.public_id}/index.html">Jane</a>'
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    source = Source()
    citation = Citation(source=source)
    person = Person(id="P0")
    person_name = PersonName(person=person, individual="Jane", citations=[citation])
    expected = "Jane"
    async with assert_template_file(
        data={
            "entity": person_name,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_private() -> None:
    person = Person(id="P0")
    person_name = PersonName(person=person, individual="Jane", privacy=Privacy.PRIVATE)
    expected = f'<a href="/person/{person.public_id}/index.html"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></a>'
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_private_person() -> None:
    person = Person(id="P0", privacy=Privacy.PRIVATE)
    person_name = PersonName(person=person, individual="Jane")
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_person_is_context() -> None:
    person = Person(id="P0")
    person_name = PersonName(person=person, individual="Jane")
    expected = "Jane"
    async with assert_template_file(
        data={
            "entity": person_name,
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_citations() -> None:
    source = Source()
    citation = Citation(source=source)
    person = Person()
    person_name = PersonName(person=person, individual="Jane", citations=[citation])
    expected = 'Jane <sup><a href="#reference-1">[1]</a></sup>'
    async with assert_template_file(
        data={
            "entity": person_name,
        },
        extensions={RaspberryMint},
        template="entity/label--person-name.html.j2",
    ) as (actual, _):
        assert actual == expected
