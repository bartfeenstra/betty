from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import TYPE_CHECKING, TypeAlias

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type import EventType
from betty.ancestry.event_type.event_types import (
    CreatableDerivableEventType,
    DerivableEventType,
)
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date, DateLike, DateRange
from betty.deriver import Deriver
from betty.model.collections import record_added
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.test_utils.ancestry.event_type import DummyEventType

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from betty.app import App
    from betty.plugin import PluginIdentifier

NewProject: TypeAlias = Callable[
    [Iterable[type[EventType]]], AbstractAsyncContextManager[Project]
]


class Ignored(DummyEventType):
    pass


class ComesBeforeReference(DummyEventType):
    pass


class ComesAfterReference(DummyEventType):
    pass


class ComesBeforeDerivable(DummyEventType, DerivableEventType):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(ComesBeforeDerivable, CreatableDerivableEventType):
    pass


class ComesAfterDerivable(DummyEventType, DerivableEventType):
    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(ComesAfterDerivable, CreatableDerivableEventType):
    pass


class ComesBeforeAndAfterDerivable(DummyEventType, DerivableEventType):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[EventType]]:
        return {Ignored}

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[EventType]]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(
    DummyEventType, CreatableDerivableEventType
):
    pass


class MayNotCreateComesAfterCreatableDerivable(ComesAfterCreatableDerivable):
    @override
    @classmethod
    async def may_create(cls, project: Project, person: Person) -> bool:
        return False


class TestDeriver:
    @pytest.fixture
    def new_project(self, new_temporary_app: App) -> NewProject:
        @asynccontextmanager
        async def _new_project(
            event_types: Iterable[type[EventType]],
        ) -> AsyncIterator[Project]:
            async with Project.new_temporary(new_temporary_app) as project, project:
                project.event_type_repository = StaticPluginRepository(
                    EventType,
                    *event_types,
                )
                yield project

        return _new_project

    @pytest.fixture
    async def project(self, new_project: NewProject) -> AsyncIterator[Project]:
        async with new_project(
            {
                ComesAfterCreatableDerivable,
                ComesAfterDerivable,
                ComesBeforeAndAfterCreatableDerivable,
                ComesBeforeAndAfterDerivable,
                ComesBeforeCreatableDerivable,
                ComesBeforeDerivable,
                ComesAfterReference,
                ComesBeforeReference,
                Ignored,
            }
        ) as project:
            yield project

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable,
            ComesBeforeCreatableDerivable,
            ComesAfterDerivable,
            ComesAfterCreatableDerivable,
            ComesBeforeAndAfterDerivable,
            ComesBeforeAndAfterCreatableDerivable,
        ],
    )
    async def test_derive__without_events(
        self, event_type: type[DerivableEventType], project: Project
    ) -> None:
        person = Person(id="P0")
        project.ancestry.add(person)

        with record_added(project.ancestry) as added:
            await Deriver(project).derive()

        assert len(added) == 0
        assert len(person.presences) == 0

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable,
            ComesBeforeCreatableDerivable,
            ComesAfterDerivable,
            ComesAfterCreatableDerivable,
            ComesBeforeAndAfterDerivable,
            ComesBeforeAndAfterCreatableDerivable,
        ],
    )
    async def test_derive__create_derivable_events_without_reference_events(
        self, event_type: type[DerivableEventType], project: Project
    ) -> None:
        person = Person(id="P0")
        derivable_event = Event(event_type=Ignored())
        Presence(person, Subject(), derivable_event)
        project.ancestry.add(person)

        with record_added(project.ancestry) as added:
            await Deriver(project).derive()

        assert len(added) == 0
        assert len(person.presences) == 1
        assert derivable_event.date is None

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable(),
            ComesBeforeCreatableDerivable(),
            ComesAfterDerivable(),
            ComesAfterCreatableDerivable(),
            ComesBeforeAndAfterDerivable(),
            ComesBeforeAndAfterCreatableDerivable(),
        ],
    )
    async def test_derive__update_derivable_event_without_reference_events(
        self, event_type: DerivableEventType, project: Project
    ) -> None:
        person = Person(id="P0")
        Presence(person, Subject(), Event(event_type=Ignored()))
        derivable_event = Event(event_type=event_type)
        Presence(person, Subject(), derivable_event)
        project.ancestry.add(person)

        with record_added(project.ancestry) as added:
            await Deriver(project).derive()

        assert len(added) == 0
        assert derivable_event.date is None

    @pytest.mark.parametrize(
        ("expected_date_like", "before_date_like", "derivable_date_like"),
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
    async def test_derive__update_comes_before_derivable_event(
        self,
        expected_date_like: DateLike | None,
        before_date_like: DateLike | None,
        derivable_date_like: DateLike | None,
        new_project: NewProject,
    ) -> None:
        async with new_project({ComesBeforeDerivable}) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Ignored(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesBeforeReference(),
                    date=before_date_like,
                ),
            )
            derivable_event = Event(
                event_type=ComesBeforeDerivable(),
                date=derivable_date_like,
            )
            Presence(person, Subject(), derivable_event)
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            if expected_date_like is None:
                assert expected_date_like == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_date_like", "before_date_like"),
        [
            (
                None,
                None,
            ),
            (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1)),
            (None, DateRange(None, None)),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
            ),
            (None, DateRange(Date(1970, 1, 1, fuzzy=True))),
            (None, DateRange(None, Date(1970, 1, 1))),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
            ),
        ],
    )
    async def test_derive__create_comes_before_derivable_event(
        self,
        expected_date_like: DateLike | None,
        before_date_like: DateLike | None,
        new_project: NewProject,
    ) -> None:
        async with new_project({ComesBeforeCreatableDerivable}) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Ignored(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesBeforeReference(),
                    date=before_date_like,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            if expected_date_like is None:
                assert len(added) == 0
            else:
                assert len(added[Event]) > 0
                for derived_event in added[Event]:
                    assert isinstance(
                        derived_event.event_type, ComesBeforeCreatableDerivable
                    )

                assert len(added[Presence]) > 0
                for derived_presence in added[Presence]:
                    assert isinstance(derived_presence.role, Subject)
                    assert derived_presence.event is not None
                    assert isinstance(
                        derived_presence.event.event_type,
                        ComesBeforeCreatableDerivable,
                    )
                    assert expected_date_like == derived_presence.event.date

    @pytest.mark.parametrize(
        ("expected_date_like", "after_date_like", "derivable_date_like"),
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
    async def test_derive__update_comes_after_derivable_event(
        self,
        expected_date_like: DateLike | None,
        after_date_like: DateLike | None,
        derivable_date_like: DateLike | None,
        new_project: NewProject,
    ) -> None:
        async with new_project({ComesAfterDerivable}) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Ignored(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date_like,
                ),
            )
            derivable_event = Event(
                event_type=ComesAfterDerivable(),
                date=derivable_date_like,
            )
            Presence(person, Subject(), derivable_event)
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            if expected_date_like is None:
                assert expected_date_like == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_date_like", "after_date_like"),
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
    async def test_derive__create_comes_after_derivable_event(
        self,
        expected_date_like: DateLike | None,
        after_date_like: DateLike | None,
        new_project: NewProject,
    ) -> None:
        async with new_project({ComesAfterCreatableDerivable}) as project:
            person = Person(id="P0")
            Presence(
                person,
                Subject(),
                Event(
                    event_type=Ignored(),
                    date=Date(0, 0, 0),
                ),
            )
            Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date_like,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            if expected_date_like is None:
                assert len(added) == 0
            else:
                assert len(added[Event]) > 0
                for derived_event in added[Event]:
                    assert isinstance(
                        derived_event.event_type, ComesAfterCreatableDerivable
                    )

                assert len(added[Presence]) > 0
                for derived_presence in added[Presence]:
                    assert isinstance(derived_presence.role, Subject)
                    assert derived_presence.event is not None
                    assert isinstance(
                        derived_presence.event.event_type,
                        ComesAfterCreatableDerivable,
                    )
                    assert expected_date_like == derived_presence.event.date

    @pytest.mark.parametrize(
        "after_date_like",
        [
            (None,),
            (Date(),),
            (Date(1970, 1, 1),),
            (DateRange(Date(1970, 1, 1)),),
            (DateRange(None, Date(1999, 12, 31)),),
            (DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),),
            (DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),),
        ],
    )
    async def test_derive__may_not_create(
        self, after_date_like: DateLike | None, new_project: NewProject
    ) -> None:
        async with new_project({MayNotCreateComesAfterCreatableDerivable}) as project:
            person = Person(id="P0")
            presence = Presence(
                person,
                Subject(),
                Event(
                    event_type=ComesAfterReference(),
                    date=after_date_like,
                ),
            )
            project.ancestry.add(person)

            with record_added(project.ancestry) as added:
                await Deriver(project).derive()

            assert len(added) == 0
            assert [*person.presences] == [presence]
