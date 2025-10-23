from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Death, Residence
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date, DateRange
from betty.model.collections import record_added
from betty.project import Project
from betty.project.extension.deriver import Deriver
from betty.project.load import load
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App
    from betty.project.extension import Extension


class TestDeriver(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, temporary_app: App) -> Extension:
        async with Project.new_temporary(temporary_app) as project, project:
            return await Deriver.new_for_project(project)

    async def test_post_load(self, temporary_app: App) -> None:
        person = Person(id="P0")
        event = Event(
            event_type=Residence(),
            date=Date(1, 1, 1),
        )
        Presence(person, Subject(), event)

        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Deriver)
            project.ancestry.add(person)
            async with project:
                with record_added(project.ancestry) as added:
                    await load(project)

                assert len(person.presences) == 3
                start = [
                    presence
                    for presence in person.presences
                    if presence.event.event_type.plugin.id == Birth.plugin.id
                    or presence.event.event_type.plugin.indicates == Birth.plugin.id
                ][0]
                assert start is not None
                assert start.event is not None
                assert isinstance(start.event, Event)
                assert (
                    DateRange(None, Date(1, 1, 1), end_is_boundary=True)
                    == start.event.date
                )
                end = [
                    presence
                    for presence in person.presences
                    if presence.event.event_type.plugin.id == Death.plugin.id
                    or presence.event.event_type.plugin.indicates == Death.plugin.id
                ][0]
                assert end is not None
                assert end.event is not None
                assert (
                    DateRange(Date(1, 1, 1), start_is_boundary=True) == end.event.date
                )
                assert len(added[Event]) == 2
                assert start.event in added[Event]
                assert end.event in added[Event]
