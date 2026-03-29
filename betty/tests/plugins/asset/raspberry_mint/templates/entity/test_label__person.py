from betty.document import Document, EntityContexts
from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
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


async def test_with_name(assert_template_file: AssertTemplateFile) -> None:
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


async def test_with_persistent_id(assert_template_file: AssertTemplateFile) -> None:
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


async def test_embedded(assert_template_file: AssertTemplateFile) -> None:
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


async def test_private(assert_template_file: AssertTemplateFile) -> None:
    person = Person(id="P0", privacy=Privacy.PRIVATE)
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


async def test_with_private_name(assert_template_file: AssertTemplateFile) -> None:
    person = Person()
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
        privacy=Privacy.PRIVATE,
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


async def test_person_is_context(assert_template_file: AssertTemplateFile) -> None:
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
