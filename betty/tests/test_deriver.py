from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, final, override

import pytest

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.date import Date, DateRange, ResolvableDate
from betty.deriver import Deriver
from betty.event_type import (
    EventType,
    EventTypeDefinition,
    ShouldExistEventType,
)
from betty.model.collections import record_added
from betty.plugin import ResolvableDefinition
from betty.project import Project
from betty.role.roles import Subject
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from betty.app import App

type NewProject = Callable[
    [Iterable[ResolvableDefinition[EventTypeDefinition]]],
    AbstractAsyncContextManager[Project],
]


@final
@EventTypeDefinition(
    "isolated",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class Isolated(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-before-reference",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class ComesBeforeReference(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-after-reference",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class ComesAfterReference(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-before",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
)
class ComesBefore(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-before-should-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
)
class ComesBeforeShouldExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True


@final
@EventTypeDefinition(
    "comes-before-should-not-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
)
class ComesBeforeShouldNotExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return False


@final
@EventTypeDefinition(
    "comes-before-and-after",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
    comes_after={ComesAfterReference},
)
class ComesBeforeAndAfter(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-before-and-after-should-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
    comes_after={ComesAfterReference},
)
class ComesBeforeAndAfterShouldExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True


@final
@EventTypeDefinition(
    "comes-before-and-after-should-not-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_before={ComesBeforeReference},
    comes_after={ComesAfterReference},
)
class ComesBeforeAndAfterShouldNotExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return False


@final
@EventTypeDefinition(
    "comes-after",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_after={ComesAfterReference},
)
class ComesAfter(EventType):
    pass


@final
@EventTypeDefinition(
    "comes-after-should-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_after={ComesAfterReference},
)
class ComesAfterShouldExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return True


@final
@EventTypeDefinition(
    "comes-after-should-not-exist",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    comes_after={ComesAfterReference},
)
class ComesAfterShouldNotExist(ShouldExistEventType):
    @override
    @classmethod
    async def should_exist(cls, project: Project, person: Person) -> bool:
        return False


class TestDeriver:
    @pytest.fixture
    def new_project(self, isolated_app: App) -> NewProject:
        @asynccontextmanager
        async def _new_project(
            event_types: Iterable[ResolvableDefinition[EventTypeDefinition]],
        ) -> AsyncIterator[Project]:
            with EventTypeDefinition.type().discoverer.override(*event_types):
                async with Project.new_isolated(isolated_app) as project, project:
                    yield project

        return _new_project

    @pytest.fixture
    async def project(self, new_project: NewProject) -> AsyncIterator[Project]:
        async with new_project(
            {
                Isolated,
                ComesBeforeReference,
                ComesBefore,
                ComesBeforeShouldExist,
                ComesBeforeShouldNotExist,
                ComesAfterReference,
                ComesAfter,
                ComesAfterShouldExist,
                ComesAfterShouldNotExist,
                ComesBeforeAndAfter,
                ComesBeforeAndAfterShouldExist,
                ComesBeforeAndAfterShouldNotExist,
            }
        ) as project:
            yield project

    async def test_derive__without_events(self, project: Project) -> None:
        person = Person(id="P0")
        project.ancestry.add(person)

        with record_added(project.ancestry) as added:
            await Deriver(project).derive()

        assert len(added) == 0
        assert len(person.presences) == 0

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeReference(),
            ComesBefore(),
            ComesBeforeShouldExist(),
            ComesBeforeShouldNotExist(),
            ComesAfterReference(),
            ComesAfter(),
            ComesAfterShouldExist(),
            ComesAfterShouldNotExist(),
            ComesBeforeAndAfter(),
            ComesBeforeAndAfterShouldExist(),
            ComesBeforeAndAfterShouldNotExist(),
        ],
    )
    async def test_derive__without_reference_events(
        self, event_type: EventType, project: Project
    ) -> None:
        person = Person(id="P0")
        derivable_event = Event(event_type=event_type)
        Presence(person, Subject(), derivable_event)
        project.ancestry.add(person)

        with record_added(project.ancestry) as added:
            await Deriver(project).derive()

        assert len(added) == 0
        assert len(person.presences) == 1
        assert derivable_event.date is None

    @pytest.mark.parametrize(
        ("expected_date", "before_date", "derivable_date"),
        [
            (None, None, None),
            (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
            (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                None,
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                None,
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                Date(1970, 1, 1),
                None,
            ),
            (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                None,
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                None,
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                None,
            ),
            (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1)),
            ),
            (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
            (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
            (
                DateRange(None, Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                None,
            ),
            (
                Date(2000, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(2000, 1, 1),
            ),
            (
                Date(1969, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(1969, 1, 1),
            ),
            (Date(2000, 1, 1), None, Date(2000, 1, 1)),
            (Date(1969, 1, 1), None, Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                None,
            ),
        ],
    )
    async def test_derive__update_comes_before(
        self,
        expected_date: ResolvableDate | None,
        before_date: ResolvableDate | None,
        derivable_date: ResolvableDate | None,
        new_project: NewProject,
    ) -> None:
        async with new_project(
            {
                ComesBefore,
                ComesBeforeReference,
            }
        ) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Isolated(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesBeforeReference(),
                    date=before_date,
                ),
            )
            derivable_event = Event(
                event_type=ComesBefore(),
                date=derivable_date,
            )
            Presence(person, Subject(), derivable_event)
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            if expected_date is None:
                assert expected_date == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_date", "before_date"),
        [
            (
                None,
                None,
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                Date(1970, 1, 1),
            ),
            (
                None,
                DateRange(None, None),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
            ),
            (
                None,
                DateRange(Date(1970, 1, 1, fuzzy=True)),
            ),
            (
                None,
                DateRange(None, Date(1970, 1, 1)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
            ),
        ],
    )
    async def test_derive__create_comes_before(
        self,
        expected_date: ResolvableDate | None,
        before_date: ResolvableDate | None,
        new_project: NewProject,
    ) -> None:
        async with new_project(
            {
                ComesBeforeShouldExist,
                ComesBeforeReference,
            }
        ) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Isolated(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesBeforeReference(),
                    date=before_date,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            if expected_date is None:
                assert len(added) == 0
            else:
                assert len(added[Event]) > 0
                for derived_event in added[Event]:
                    assert isinstance(derived_event.event_type, ComesBeforeShouldExist)

                assert len(added[Presence]) > 0
                for derived_presence in added[Presence]:
                    assert isinstance(derived_presence.role, Subject)
                    assert derived_presence.event is not None
                    assert isinstance(
                        derived_presence.event.event_type,
                        ComesBeforeShouldExist,
                    )
                    assert expected_date == derived_presence.event.date

    @pytest.mark.parametrize(
        ("expected_date", "after_date", "derivable_date"),
        [
            (None, None, None),
            (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
            (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                None,
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                None,
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                Date(1970, 1, 1),
                None,
            ),
            (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1999, 12, 31), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                None,
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                None,
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                None,
            ),
            (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1)),
            ),
            (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
            (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                Date(1970, 1, 1),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                None,
            ),
            (
                Date(2000, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(2000, 1, 1),
            ),
            (
                Date(1969, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(1969, 1, 1),
            ),
            (Date(2000, 1, 1), None, Date(2000, 1, 1)),
            (Date(1969, 1, 1), None, Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                None,
            ),
        ],
    )
    async def test_derive__update_comes_after(
        self,
        expected_date: ResolvableDate | None,
        after_date: ResolvableDate | None,
        derivable_date: ResolvableDate | None,
        new_project: NewProject,
    ) -> None:
        async with new_project(
            {
                ComesAfter,
                ComesAfterReference,
            }
        ) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Isolated(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date,
                ),
            )
            derivable_event = Event(
                event_type=ComesAfter(),
                date=derivable_date,
            )
            Presence(person, Subject(), derivable_event)
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            if expected_date is None:
                assert expected_date == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_date", "after_date"),
        [
            (None, None),
            (None, Date()),
            (DateRange(Date(1970, 1, 1), start_is_boundary=True), Date(1970, 1, 1)),
            (None, DateRange(Date(1970, 1, 1))),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(None, Date(1999, 12, 31)),
            ),
            (None, DateRange(None, Date(1999, 12, 31, fuzzy=True))),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),
            ),
        ],
    )
    async def test_derive__create_comes_after(
        self,
        expected_date: ResolvableDate | None,
        after_date: ResolvableDate | None,
        new_project: NewProject,
    ) -> None:
        async with new_project(
            {
                ComesAfterShouldExist,
                ComesAfterReference,
            }
        ) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Isolated(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            if expected_date is None:
                assert len(added) == 0
            else:
                assert len(added[Event]) > 0
                for derived_event in added[Event]:
                    assert isinstance(derived_event.event_type, ComesAfterShouldExist)

                assert len(added[Presence]) > 0
                for derived_presence in added[Presence]:
                    assert isinstance(derived_presence.role, Subject)
                    assert derived_presence.event is not None
                    assert isinstance(
                        derived_presence.event.event_type,
                        ComesAfterShouldExist,
                    )
                    assert expected_date == derived_presence.event.date

    @pytest.mark.parametrize(
        "after_date",
        [
            None,
            Date(),
            Date(1970, 1, 1),
            DateRange(Date(1970, 1, 1)),
            DateRange(None, Date(1999, 12, 31)),
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
            DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),
        ],
    )
    async def test_derive__should_not_exist(
        self, after_date, new_project: NewProject
    ) -> None:
        async with new_project(
            {
                ComesBeforeReference,
                ComesBeforeShouldNotExist,
                ComesAfterReference,
                ComesAfterShouldNotExist,
                ComesBeforeAndAfterShouldNotExist,
            }
        ) as project:
            person = Person(id="P0")
            presence = Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            assert [*person.presences] == [presence]
