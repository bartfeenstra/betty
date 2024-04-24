from __future__ import annotations

from typing import Any, Iterator

import pytest

from betty.extension.cotton_candy import (
    _ColorConfiguration,
    CottonCandyConfiguration,
    person_timeline_events,
)
from betty.locale import Datey, Date, DateRange
from betty.model import (
    Entity,
    get_entity_type_name,
    UserFacingEntity,
    GeneratedEntityId,
)
from betty.model.ancestry import (
    Person,
    Presence,
    Subject,
    Event,
    PresenceRole,
    Attendee,
    Privacy,
)
from betty.model.event_type import Birth, UnknownEventType, EventType, Death
from betty.project import EntityReference, DEFAULT_LIFETIME_THRESHOLD
from betty.serde.dump import Dump
from betty.serde.load import AssertionFailed
from betty.tests.serde import raises_error


class TestColorConfiguration:
    async def test_hex_with_valid_value(self) -> None:
        hex_value = "#000000"
        sut = _ColorConfiguration("#ffffff")
        sut.hex = hex_value
        assert hex_value == sut.hex

    @pytest.mark.parametrize(
        "hex_value",
        [
            "rgb(0,0,0)",
            "pink",
        ],
    )
    async def test_hex_with_invalid_value(self, hex_value: str) -> None:
        sut = _ColorConfiguration("#ffffff")
        with pytest.raises(AssertionFailed):
            sut.hex = hex_value

    async def test_load_with_valid_hex_value(self) -> None:
        hex_value = "#000000"
        dump = hex_value
        sut = _ColorConfiguration("#ffffff").load(dump)
        assert hex_value == sut.hex

    @pytest.mark.parametrize(
        "dump",
        [
            False,
            123,
            "rgb(0,0,0)",
            "pink",
        ],
    )
    async def test_load_with_invalid_value(self, dump: Dump) -> None:
        sut = _ColorConfiguration("#ffffff")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_with_value(self) -> None:
        hex_value = "#000000"
        assert hex_value == _ColorConfiguration(hex_value=hex_value).dump()


class CottonCandyConfigurationTestEntity(UserFacingEntity, Entity):
    pass


class CottonCandyConfigurationTestEntitytest_load_with_featured_entities:
    pass


class TestCottonCandyConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: dict[str, Any] = {}
        CottonCandyConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            CottonCandyConfiguration().load(dump)

    async def test_load_with_featured_entities(self) -> None:
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = "123"
        dump: Dump = {
            "featured_entities": [
                {
                    "entity_type": get_entity_type_name(entity_type),
                    "entity_id": entity_id,
                },
            ],
        }
        sut = CottonCandyConfiguration.load(dump)
        assert entity_type is sut.featured_entities[0].entity_type
        assert entity_id == sut.featured_entities[0].entity_id

    async def test_load_with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration.load(dump)
        assert hex_value == sut.primary_inactive_color.hex

    async def test_load_with_primary_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "primary_active_color": hex_value,
        }
        sut = CottonCandyConfiguration.load(dump)
        assert hex_value == sut.primary_active_color.hex

    async def test_load_with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_inactive_color": hex_value,
        }
        sut = CottonCandyConfiguration.load(dump)
        assert hex_value == sut.link_inactive_color.hex

    async def test_load_with_link_active_color(self) -> None:
        hex_value = "#000000"
        dump: Dump = {
            "link_active_color": hex_value,
        }
        sut = CottonCandyConfiguration.load(dump)
        assert hex_value == sut.link_active_color.hex

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = CottonCandyConfiguration()
        expected = {
            "primary_inactive_color": CottonCandyConfiguration.DEFAULT_PRIMARY_INACTIVE_COLOR,
            "primary_active_color": CottonCandyConfiguration.DEFAULT_PRIMARY_ACTIVE_COLOR,
            "link_inactive_color": CottonCandyConfiguration.DEFAULT_LINK_INACTIVE_COLOR,
            "link_active_color": CottonCandyConfiguration.DEFAULT_LINK_ACTIVE_COLOR,
        }
        assert expected == sut.dump()

    async def test_dump_with_featured_entities(self) -> None:
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = "123"
        sut = CottonCandyConfiguration(
            featured_entities=[EntityReference(entity_type, entity_id)],
        )
        expected = [
            {
                "entity_type": get_entity_type_name(entity_type),
                "entity_id": entity_id,
            },
        ]
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert expected == dump["featured_entities"]

    async def test_dump_with_primary_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_inactive_color"]

    async def test_dump_with_primary_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(primary_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["primary_active_color"]

    async def test_dump_with_link_inactive_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_inactive_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_inactive_color"]

    async def test_dump_with_link_active_color(self) -> None:
        hex_value = "#000000"
        sut = CottonCandyConfiguration(link_active_color=hex_value)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert hex_value == dump["link_active_color"]


__REFERENCE_DATE = Date(1970, 1, 1)
_REFERENCE_DATES = (
    __REFERENCE_DATE,
    DateRange(__REFERENCE_DATE),
    DateRange(None, __REFERENCE_DATE),
)
_BEFORE_REFERENCE_DATE = Date(1900, 1, 1)
_AFTER_REFERENCE_DATE = Date(2000, 1, 1)


def _parameterize_with_associated_events() -> Iterator[
    tuple[
        bool,
        PresenceRole,
        str | None,
        Privacy,
        type[EventType],
        Datey | None,
        Privacy,
        type[EventType],
        Datey | None,
    ]
]:
    ids = (
        (True, "E1"),
        (False, None),
    )
    privacies = (
        (True, Privacy.PUBLIC),
        (False, Privacy.PRIVATE),
    )
    person_event_reference_dateys = (
        *((True, reference_date) for reference_date in _REFERENCE_DATES),
        (False, None),
    )
    person_presence_roles = (
        (True, Subject()),
        (False, Attendee()),
    )
    event_types = (
        (True, Birth),
        (False, UnknownEventType),
    )
    event_dateys_and_person_reference_event_types = (
        (True, _AFTER_REFERENCE_DATE, Birth),
        (False, _BEFORE_REFERENCE_DATE, Birth),
        (True, _BEFORE_REFERENCE_DATE, Death),
        (False, _AFTER_REFERENCE_DATE, Death),
    )
    for event_id_expected, event_id in ids:
        for event_privacy_expected, event_privacy in privacies:
            for (
                person_reference_event_privacy_expected,
                person_reference_event_privacy,
            ) in privacies:
                for (
                    person_reference_event_datey_expected,
                    person_reference_event_datey,
                ) in person_event_reference_dateys:
                    for (
                        person_presence_role_expected,
                        person_presence_role,
                    ) in person_presence_roles:
                        for (
                            event_datey_and_person_reference_event_type_expected,
                            event_datey,
                            person_reference_event_type,
                        ) in event_dateys_and_person_reference_event_types:
                            for event_type_expected, event_type in event_types:
                                yield (
                                    all(
                                        (
                                            person_presence_role_expected,
                                            event_id_expected,
                                            event_privacy_expected,
                                            event_type_expected,
                                            event_datey_and_person_reference_event_type_expected,
                                            person_reference_event_privacy_expected,
                                            person_reference_event_datey_expected,
                                        )
                                    ),
                                    person_presence_role,
                                    event_id,
                                    event_privacy,
                                    event_type,
                                    event_datey,
                                    person_reference_event_privacy,
                                    person_reference_event_type,
                                    person_reference_event_datey,
                                )


class TestPersonLifetimeEvents:
    @pytest.mark.parametrize(
        "expected, event_id, event_privacy, event_datey",
        [
            # Events without dates are omitted from timelines.
            (False, "E1", Privacy.PUBLIC, None),
            (True, "E1", Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with generated IDs are included if they are the person's own.
            (True, None, Privacy.PUBLIC, Date(1970, 1, 1)),
            # Events with non-comparable dates are omitted from timelines.
            (False, "E1", Privacy.PUBLIC, Date(None, 1, 1)),
            # Private events are omitted from timelines.
            (False, "E1", Privacy.PRIVATE, Date(1970, 1, 1)),
        ],
    )
    async def test_with_person_event(
        self,
        expected: bool,
        event_id: str | None,
        event_privacy: Privacy,
        event_datey: Datey | None,
    ) -> None:
        person = Person()
        event = Event(
            id=event_id,
            event_type=UnknownEventType,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(person, Attendee(), event)
        actual = list(person_timeline_events(person, DEFAULT_LIFETIME_THRESHOLD))
        assert expected is (event in actual)

    @pytest.mark.parametrize(
        (
            "expected",
            "presence_role",
            "event_id",
            "event_privacy",
            "event_type",
            "event_datey",
            "person_reference_event_privacy",
            "person_reference_event_type",
            "person_reference_event_datey",
        ),
        _parameterize_with_associated_events(),
    )
    async def test_with_associated_events(
        self,
        expected: bool,
        presence_role: PresenceRole,
        event_id: str | None,
        event_privacy: Privacy,
        event_type: type[EventType],
        event_datey: Datey | None,
        person_reference_event_privacy: Privacy,
        person_reference_event_type: type[EventType],
        person_reference_event_datey: Datey | None,
    ) -> None:
        event_ids = 0

        def _event_id(event_id: str | None) -> str | None:
            nonlocal event_ids

            if event_id is None:
                return None
            if isinstance(event_id, GeneratedEntityId):
                return event_id
            event_ids += 1
            return f"{event_id}-{event_ids}"

        person = Person()
        person_reference_event = Event(
            id=_event_id(event_id),
            event_type=person_reference_event_type,
            date=person_reference_event_datey,
            privacy=person_reference_event_privacy,
        )
        Presence(person, Subject(), person_reference_event)

        ancestor1 = Person()
        ancestor1.children.add(person)
        ancestor2 = Person()
        ancestor2.children.add(ancestor1)
        ancestor3 = Person()
        ancestor3.children.add(ancestor2)
        ancestor3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(ancestor3, presence_role, ancestor3_event)

        descendant1 = Person()
        descendant1.parents.add(person)
        descendant2 = Person()
        descendant2.parents.add(descendant1)
        descendant3 = Person()
        descendant3.parents.add(descendant2)
        descendant3_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(descendant3, presence_role, descendant3_event)

        sibling = Person()
        sibling.parents.add(ancestor1)
        sibling_event = Event(
            id=_event_id(event_id),
            event_type=event_type,
            date=event_datey,
            privacy=event_privacy,
        )
        Presence(sibling, presence_role, sibling_event)

        actual = list(person_timeline_events(person, DEFAULT_LIFETIME_THRESHOLD))
        assert expected is (ancestor3_event in actual)
        assert expected is (descendant3_event in actual)
        assert expected is (sibling_event in actual)
