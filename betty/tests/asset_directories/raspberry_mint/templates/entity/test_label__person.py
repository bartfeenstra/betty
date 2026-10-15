from betty.document import Document, EntityContexts
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person()
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == expected


async def test_with_name(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person()
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = "Jane Dough"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == expected


async def test_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person(id="my-first-person")
    expected = f'<a href="/person/{person.id}/index.html"><span title="This person\'s name is unknown.">n.n.</span></a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == expected


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(id="my-first-person")
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person, "embedded": True}
    ) as rendered:
        assert rendered == expected


async def test_private(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == expected


async def test_with_private_name(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person()
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
        privacy=Privacy.PRIVATE,
    )
    expected = '<span class="private" title="This information is unavailable to protect people\'s privacy.">private</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == expected


async def test_person_is_context(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(id="my-first-person")
    expected = '<span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--person.html.j2",
        data={
            "entity": person,
            "document": Document(entity_contexts=EntityContexts(person)),
        },
    ) as rendered:
        assert rendered == expected
