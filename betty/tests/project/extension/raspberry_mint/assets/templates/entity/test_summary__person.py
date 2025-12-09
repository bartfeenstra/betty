from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Death
from betty.ancestry.gender.genders import NonBinary
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    person = Person()
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert actual == '<div class="small"></div>'


async def test_embedded() -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Jane", citations=[Citation(source=source)])
    birth = Event(event_type=Birth(), citations=[Citation(source=source)])
    death = Event(event_type=Death(), citations=[Citation(source=source)])
    Presence(person, Subject(), birth)
    Presence(person, Subject(), death)
    async with assert_template_file(
        data={
            "entity": person,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert birth.id not in actual
        assert death.id not in actual
        assert "#reference" not in actual


async def test_private() -> None:
    source = Source()
    person = Person(private=True)
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
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert individual_name not in actual
        assert birth.event_type.plugin().label.localize(DEFAULT_LOCALIZER) not in actual
        assert death.event_type.plugin().label.localize(DEFAULT_LOCALIZER) not in actual
        assert "#reference" not in actual


async def test_with_public_alternative_name() -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Primary Name")
    individual_name = "Jane"
    PersonName(
        person=person,
        individual=individual_name,
        citations=[Citation(source=source)],
    )
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert individual_name in actual
        assert "#reference" in actual


async def test_with_private_alternative_name() -> None:
    source = Source()
    person = Person()
    PersonName(person=person, individual="Primary Name")
    individual_name = "Jane"
    PersonName(
        person=person,
        individual=individual_name,
        citations=[Citation(source=source)],
        private=True,
    )
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert individual_name not in actual
        assert "#reference" not in actual


async def test_with_birh_indicator() -> None:
    source = Source()
    person = Person()
    birth = Event(event_type=Birth(), citations=[Citation(source=source)])
    Presence(person, Subject(), birth)
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert birth.event_type.plugin().label.localize(DEFAULT_LOCALIZER) in actual
        assert "#reference" in actual


async def test_with_death_indicator() -> None:
    source = Source()
    person = Person()
    death = Event(event_type=Death(), citations=[Citation(source=source)])
    Presence(person, Subject(), death)
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert death.event_type.plugin().label.localize(DEFAULT_LOCALIZER) in actual
        assert "#reference" in actual


async def test_with_gender() -> None:
    person = Person(gender=NonBinary())
    async with assert_template_file(
        data={
            "entity": person,
        },
        extensions={RaspberryMint},
        template="entity/summary--person.html.j2",
    ) as (actual, _):
        assert NonBinary.plugin().label.localize(DEFAULT_LOCALIZER) in actual
