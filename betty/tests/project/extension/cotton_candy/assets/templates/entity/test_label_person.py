from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.jinja2 import EntityContexts
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_with_name() -> None:
    person = Person(id="P0")
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_without_name() -> None:
    person = Person(id="P0")
    expected = '<a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded() -> None:
    person = Person(id="P0")
    expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": person,
            "embedded": True,
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_person_is_context() -> None:
    person = Person(id="P0")
    expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": person,
            "entity_contexts": await EntityContexts.new(person),
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_private() -> None:
    person = Person(
        id="P0",
        private=True,
    )
    expected = '<span class="private" title="This person\'s details are unavailable to protect their privacy.">private</span>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_entity() -> None:
    person = Person(id="P0")
    PersonName(
        person=person,
        individual="Jane",
        affiliation="Dough",
    )
    expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={CottonCandy},
        template="entity/label--person.html.j2",
    ) as (actual, _):
        assert actual == expected
