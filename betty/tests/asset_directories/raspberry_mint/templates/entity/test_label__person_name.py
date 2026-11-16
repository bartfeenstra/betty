from betty.document import Document, EntityContexts
from betty.entities.citation import Citation
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.source import Source
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertJinja


async def test_minimal_with_individual_name(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person()
    person_name = PersonName(person=person, individual="Jane")
    expected = "Jane"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected


async def test_minimal_with_affiliation_name(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person()
    person_name = PersonName(person=person, affiliation="Dough")
    expected = "… Dough"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected


async def test_with_person_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person(id="my-first-person")
    person_name = PersonName(person=person, individual="Jane")
    expected = f'<a href="/person/{person.id}/index.html">Jane</a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source)
    person = Person(id="my-first-person")
    person_name = PersonName(person=person, individual="Jane", citations=[citation])
    expected = "Jane"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2",
        data={"entity": person_name, "embedded": True},
    ) as rendered:
        assert rendered == expected


async def test_private(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(id="my-first-person")
    person_name = PersonName(person=person, individual="Jane", privacy=Privacy.PRIVATE)
    expected = f'<a href="/person/{person.id}/index.html"><span class="private" title="This information is unavailable to protect people\'s privacy.">private</span></a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected


async def test_with_private_person(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    person_name = PersonName(person=person, individual="Jane")
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected


async def test_person_is_context(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(id="my-first-person")
    person_name = PersonName(person=person, individual="Jane")
    expected = "Jane"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2",
        data={
            "entity": person_name,
            "document": Document(entity_contexts=EntityContexts(person)),
        },
    ) as rendered:
        assert rendered == expected


async def test_with_citations(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    citation = Citation(source=source)
    person = Person()
    person_name = PersonName(person=person, individual="Jane", citations=[citation])
    expected = 'Jane <sup><a href="#reference-1">[1]</a></sup>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person-name.html.j2", data={"entity": person_name}
    ) as rendered:
        assert rendered == expected
