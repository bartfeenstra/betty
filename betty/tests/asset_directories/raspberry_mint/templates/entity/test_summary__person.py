from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.person_name import PersonName
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.genders.non_binary import NonBinary
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.roles.subject import Subject
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person()
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert rendered == '<div class="small"></div>'


async def test_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Jane", citations=[Citation(source=source)])
    birth = Event(event_type=Birth(), citations=[Citation(source=source)])
    death = Event(event_type=Death(), citations=[Citation(source=source)])
    Presence(person, Subject(), birth)
    Presence(person, Subject(), death)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person, "embedded": True}
    ) as rendered:
        assert birth.id not in rendered
        assert death.id not in rendered
        assert "#reference" not in rendered


async def test_private(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    source = Source()
    person = Person(privacy=Privacy.PRIVATE)
    PersonName(person=person, individual="Primary Name")
    individual_name = "Jane"
    PersonName(
        person=person,
        individual=individual_name,
        citations=[Citation(source=source)],
    )
    birth = Event(event_type=Birth(), citations=[Citation(source=source)])
    death = Event(event_type=Death(), citations=[Citation(source=source)])
    Presence(person, Subject(), birth)
    Presence(person, Subject(), death)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert individual_name not in rendered
        assert (
            birth.event_type.definition.label.localize(default_localizer)
            not in rendered
        )
        assert (
            death.event_type.definition.label.localize(default_localizer)
            not in rendered
        )
        assert "#reference" not in rendered


async def test_with_public_alternative_name(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Primary Name")
    individual_name = "Jane"
    PersonName(
        person=person,
        individual=individual_name,
        citations=[Citation(source=source)],
    )
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert individual_name in rendered
        assert "#reference" in rendered


async def test_with_private_alternative_name(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Primary Name")
    individual_name = "Jane"
    PersonName(
        person=person,
        individual=individual_name,
        citations=[Citation(source=source)],
        privacy=Privacy.PRIVATE,
    )
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert individual_name not in rendered
        assert "#reference" not in rendered


async def test_with_birh_indicator(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    person = Person()
    birth = Event(event_type=Birth(), citations=[Citation(source=source)])
    Presence(person, Subject(), birth)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert birth.event_type.definition.label.localize(default_localizer) in rendered
        assert "#reference" in rendered


async def test_with_death_indicator(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    source = Source()
    person = Person()
    death = Event(event_type=Death(), citations=[Citation(source=source)])
    Presence(person, Subject(), death)
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert death.event_type.definition.label.localize(default_localizer) in rendered
        assert "#reference" in rendered


async def test_with_gender(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person(gender=NonBinary())
    async with assert_raspberry_mint_jinja_file(
        "entity/summary--person.html.j2", data={"entity": person}
    ) as rendered:
        assert NonBinary.definition.label.localize(default_localizer) in rendered
