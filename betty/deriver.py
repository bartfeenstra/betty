"""
Provide an API to derive information from ancestries, and create new entities or update existing ones.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, cast, final
from uuid import NAMESPACE_URL, uuid5

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type import EventTypeDefinition, ShouldExistEventType
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date, DateRange
from betty.locale.localizable import _
from betty.plugin.ordered import get_comes_after, get_comes_before

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Sequence

    from betty.project import Project


class Derivation(Enum):
    """
    Derivation types.
    """

    #: No derivation took place.
    NONE = 1

    #: The derivation created new data.
    CREATE = 2

    #: The derivation updated existing data.
    UPDATE = 3


def _derive_event_id(derivable_event_type: EventTypeDefinition, person: Person) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"betty-deriver://{derivable_event_type.id}/{person.id}",
        )
    )


@final
class Deriver:
    """
    Derive information from ancestries, and create new entities or update existing ones.
    """

    def __init__(self, project: Project):
        super().__init__()
        self._project = project

    async def derive(self) -> None:
        """
        Derive additional data.
        """
        for derivable_event_type in await self._project.plugins(EventTypeDefinition):
            created_derivations = 0
            updated_derivations = 0
            for person in self._project.ancestry[Person]:
                created, updated = await self._derive_person(
                    person, derivable_event_type
                )
                created_derivations += created
                updated_derivations += updated
            if updated_derivations > 0:
                await self._project.app.user.message_information_details(
                    _(
                        "Updated {updated_derivations} {event_type} events based on existing information."
                    ).format(
                        updated_derivations=str(updated_derivations),
                        event_type=derivable_event_type.label,
                    )
                )
            if created_derivations > 0:
                await self._project.app.user.message_information_details(
                    _(
                        "Created {created_derivations} additional {event_type} events based on existing information."
                    ).format(
                        created_derivations=str(created_derivations),
                        event_type=derivable_event_type.label,
                    )
                )

    async def _derive_person(
        self, person: Person, derivable_event_type: EventTypeDefinition
    ) -> tuple[int, int]:
        event_types = await self._project.plugins(EventTypeDefinition)
        # Gather any existing events that could be derived, or create a new derived event if needed.
        derivable_events: Sequence[tuple[Event, Derivation]] = [
            (event, Derivation.UPDATE)
            for event in _get_derivable_events(person, derivable_event_type)
        ]
        if not derivable_events:
            if list(
                filter(
                    lambda presence: presence.event.event_type.plugin.id
                    == derivable_event_type.id,
                    person.presences,
                )
            ):
                return 0, 0
            if issubclass(
                derivable_event_type.cls,
                ShouldExistEventType,
            ) and await derivable_event_type.cls.should_exist(self._project, person):
                derivable_events = [
                    (
                        Event(
                            id=_derive_event_id(derivable_event_type, person),
                            event_type=await self._project.new_target(
                                derivable_event_type.cls
                            ),
                        ),
                        Derivation.CREATE,
                    ),
                ]
            else:
                return 0, 0

        # Aggregate event type order from references and backreferences.
        comes_before_event_types = get_comes_before(event_types, derivable_event_type)
        comes_after_event_types = get_comes_after(event_types, derivable_event_type)

        created_derivations = 0
        updated_derivations = 0

        for derivable_event, derivation in derivable_events:
            dates_derived = False
            # We know _get_derivable_events() only returns events without a date or a with a date range, but Python
            # does not let us express that in a(n intersection) type, so we must instead cast here.
            derivable_date = cast(DateRange | None, derivable_event.date)

            if derivable_date is None or derivable_date.end is None:
                dates_derived = dates_derived or _ComesBeforeDateDeriver.derive(
                    person, derivable_event, comes_before_event_types
                )

            if derivable_date is None or derivable_date.start is None:
                dates_derived = dates_derived or _ComesAfterDateDeriver.derive(
                    person, derivable_event, comes_after_event_types
                )

            if dates_derived:
                self._project.ancestry.add(derivable_event)
                if derivation is Derivation.CREATE:
                    created_derivations += 1
                    presence = Presence(person, Subject(), derivable_event)
                    self._project.ancestry.add(presence)
                else:
                    updated_derivations += 1

        return created_derivations, updated_derivations


class _DateDeriver(ABC):
    @classmethod
    def derive(
        cls,
        person: Person,
        derivable_event: Event,
        reference_event_types: Collection[EventTypeDefinition],
    ) -> bool:
        if not reference_event_types:
            return False

        reference_events = _get_reference_events(
            person, reference_event_types, derivable_event.event_type.plugin
        )
        reference_events_dates: Iterable[tuple[Event, Date]] = filter(
            lambda x: x[1].comparable, cls._get_events_dates(reference_events)
        )
        if derivable_event.date is not None:
            reference_events_dates = filter(
                lambda x: cls._compare(cast(DateRange, derivable_event.date), x[1]),
                reference_events_dates,
            )
        sorted_reference_events_dates = cls._sort(reference_events_dates)
        try:
            reference_event, reference_date = sorted_reference_events_dates[0]
        except IndexError:
            return False

        if derivable_event.date is None:
            derivable_event.date = DateRange()
        cls._set(
            cast(DateRange, derivable_event.date),
            Date(
                reference_date.year,
                reference_date.month,
                reference_date.day,
                fuzzy=reference_date.fuzzy,
            ),
        )
        derivable_event.citations.add(*reference_event.citations)

        return True

    @classmethod
    def _get_events_dates(cls, events: Iterable[Event]) -> Iterable[tuple[Event, Date]]:
        for event in events:
            if isinstance(event.date, Date):
                yield event, event.date
            if isinstance(event.date, DateRange):
                for date in cls._get_date_range_dates(event.date):
                    yield event, date

    @classmethod
    @abstractmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        pass

    @classmethod
    @abstractmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        pass

    @classmethod
    @abstractmethod
    def _sort(
        cls, events_dates: Iterable[tuple[Event, Date]]
    ) -> Sequence[tuple[Event, Date]]:
        pass

    @classmethod
    @abstractmethod
    def _set(cls, derivable_date: DateRange, derived_date: Date) -> None:
        pass


@final
class _ComesBeforeDateDeriver(_DateDeriver):
    @override
    @classmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        if date.start is not None and not date.start_is_boundary:
            yield date.start
        if date.end is not None:
            yield date.end

    @override
    @classmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date < reference_date

    @override
    @classmethod
    def _sort(
        cls, events_dates: Iterable[tuple[Event, Date]]
    ) -> Sequence[tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1])

    @override
    @classmethod
    def _set(cls, derivable_date: DateRange, derived_date: Date) -> None:
        derivable_date.end = derived_date
        derivable_date.end_is_boundary = True


@final
class _ComesAfterDateDeriver(_DateDeriver):
    @override
    @classmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        if date.start is not None:
            yield date.start
        if date.end is not None and not date.end_is_boundary:
            yield date.end

    @override
    @classmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date > reference_date

    @override
    @classmethod
    def _sort(
        cls, events_dates: Iterable[tuple[Event, Date]]
    ) -> Sequence[tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1], reverse=True)

    @override
    @classmethod
    def _set(cls, derivable_date: DateRange, derived_date: Date) -> None:
        derivable_date.start = derived_date
        derivable_date.start_is_boundary = True


def _get_derivable_events(
    person: Person, derivable_event_type: EventTypeDefinition
) -> Iterable[Event]:
    for presence in person.presences:
        event = presence.event

        # Ignore events of the wrong type.
        if event.event_type.plugin.id != derivable_event_type.id:
            continue

        # Ignore events with enough date information that nothing more can be derived.
        if isinstance(event.date, Date):
            continue
        if (
            isinstance(event.date, DateRange)
            and (
                not event.event_type.plugin.comes_after or event.date.start is not None
            )
            and (not event.event_type.plugin.comes_before or event.date.end is not None)
        ):
            continue

        yield event


def _get_reference_events(
    person: Person,
    reference_event_types: Collection[EventTypeDefinition],
    derivable_event_type: EventTypeDefinition,
) -> Iterable[Event]:
    reference_event_type_ids = [
        reference_event_type.id for reference_event_type in reference_event_types
    ]
    for presence in person.presences:
        reference_event = presence.event

        if reference_event.date is None:
            continue

        if isinstance(reference_event.date, DateRange):
            if (
                reference_event.event_type.plugin.id
                in derivable_event_type.comes_before
            ):
                reference_date = reference_event.date.start
            else:
                reference_date = reference_event.date.end
            if reference_date is None:
                continue
            if reference_date.fuzzy:
                continue

        # Ignore reference events of the wrong type.
        if reference_event.event_type.plugin.id not in reference_event_type_ids:
            continue

        yield reference_event
