"""
Common theme functionality.

The contents of this file should eventually be stabilized and moved to more specific modules.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, cast

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Death
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import Subject
from betty.assertion import assert_str
from betty.config import Configuration
from betty.date import Date, DateLike
from betty.exception import HumanFacingException
from betty.functools import unique
from betty.locale.localizable import _
from betty.model import persistent_id
from betty.privacy import is_public

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.has_file_references import HasFileReferences
    from betty.ancestry.presence import Presence
    from betty.jinja2 import Filters
    from betty.project import Project
    from betty.serde.dump import Dump


def _is_person_timeline_presence(presence: Presence) -> bool:
    if presence.private:
        return False
    if not presence.event.date:
        return False
    if not presence.event.date.comparable:
        return False
    return True


def person_timeline_events(person: Person, lifetime_threshold: int) -> Iterable[Event]:
    """
    Gather all events for a person's timeline.
    """
    yield from unique(_person_timeline_events(person, lifetime_threshold))


def person_descendant_families(
    person: Person,
) -> Iterable[tuple[Sequence[Person], Sequence[Person]]]:
    """
    Gather a person's families they are a parent in.
    """
    parents = {}
    children = defaultdict(set)
    for child in person.children:
        family = tuple(sorted(parent.id for parent in child.parents))
        if family not in parents:
            parents[family] = tuple(child.parents)
        children[family].add(child)
    yield from zip(parents.values(), children.values(), strict=True)


def associated_file_references(
    has_file_references: HasFileReferences,
) -> Iterable[FileReference]:
    """
    Get the associated file references for an entity that has file references.
    """
    yield from unique(
        _associated_file_references(has_file_references),
        key=lambda file_reference: file_reference.file,
    )


def _associated_file_references(
    has_file_references: HasFileReferences,
) -> Iterable[FileReference]:
    yield from has_file_references.file_references

    if isinstance(has_file_references, Event):
        for citation in has_file_references.citations:
            yield from _associated_file_references(citation)

    if isinstance(has_file_references, Person):
        for name in has_file_references.names:
            for citation in name.citations:
                yield from _associated_file_references(citation)
        for presence in has_file_references.presences:
            yield from _associated_file_references(presence.event)

    if isinstance(has_file_references, Place):
        for event in has_file_references.events:
            yield from _associated_file_references(event)


def _person_timeline_events(person: Person, lifetime_threshold: int) -> Iterable[Event]:
    # Collect all associated events for a person.
    # Start with the person's own events for which their presence is public.
    for presence in person.presences:
        if _is_person_timeline_presence(presence):
            assert presence.event is not None
            yield presence.event
        continue

    # If the person has start- or end-of-life events, we use those to constrain associated people's events.
    start_dates = []
    end_dates = []
    for presence in person.presences:
        if not _is_person_timeline_presence(presence):
            continue
        assert presence.event is not None
        assert presence.event.date is not None
        if presence.role.plugin.id != Subject.plugin.id:
            continue
        if (
            presence.event.event_type.plugin.id == Birth.plugin.id
            or presence.event.event_type.plugin.indicates == Birth.plugin.id
        ):
            start_dates.append(presence.event.date)
        if (
            presence.event.event_type.plugin.id == Death.plugin.id
            or presence.event.event_type.plugin.indicates == Death.plugin.id
        ):
            end_dates.append(presence.event.date)
    start_date = sorted(start_dates)[0] if start_dates else None
    end_date = sorted(end_dates)[0] if end_dates else None

    # If an end-of-life event exists, but no start-of-life event, create a start-of-life date based on the end date,
    # minus the lifetime threshold.
    if start_date is None and end_date is not None:
        if isinstance(end_date, Date):
            start_date_reference = end_date
        else:
            if end_date.end is not None and end_date.end.comparable:
                start_date_reference = end_date.end
            else:
                assert end_date.start is not None
                start_date_reference = end_date.start
        assert start_date_reference.year is not None
        start_date = Date(
            start_date_reference.year - lifetime_threshold,
            start_date_reference.month,
            start_date_reference.day,
            start_date_reference.fuzzy,
        )

    # If a start-of-life event exists, but no end-of-life event, create an end-of-life date based on the start date,
    # plus the lifetime threshold.
    if end_date is None and start_date is not None:
        if isinstance(start_date, Date):
            end_date_reference = start_date
        else:
            if start_date.start and start_date.start.comparable:
                end_date_reference = start_date.start
            else:
                assert start_date.end is not None
                end_date_reference = start_date.end
        assert end_date_reference.year is not None
        end_date = Date(
            end_date_reference.year + lifetime_threshold,
            end_date_reference.month,
            end_date_reference.day,
            end_date_reference.fuzzy,
        )

    if start_date is None or end_date is None:
        reference_dates = sorted(
            cast(DateLike, presence.event.date)
            for presence in person.presences
            if _is_person_timeline_presence(presence)
        )
        if reference_dates:
            if not start_date:
                start_date = reference_dates[0]
            if not end_date:
                end_date = reference_dates[-1]

    if start_date is not None and end_date is not None:
        associated_people = filter(
            is_public,
            (
                # All ancestors.
                *person.ancestors,
                # All descendants.
                *person.descendants,
                # All siblings.
                *person.siblings,
            ),
        )
        for associated_person in associated_people:
            # For associated events, we are only interested in people's start- or end-of-life events.
            for associated_presence in associated_person.presences:
                if (
                    associated_presence.event.event_type.plugin.id != Birth.plugin.id
                    and associated_presence.event.event_type.plugin.id
                    != Birth.plugin.id
                    and associated_presence.event.event_type.plugin.id
                    != Death.plugin.id
                    and associated_presence.event.event_type.plugin.indicates
                    != Death.plugin.id
                ):
                    continue
                if not persistent_id(associated_presence.event):
                    continue
                if not isinstance(associated_presence.role, Subject):
                    continue
                if not _is_person_timeline_presence(associated_presence):
                    continue
                if not associated_presence.event.date:
                    continue
                if associated_presence.event.date < start_date:
                    continue
                if associated_presence.event.date > end_date:
                    continue
                yield associated_presence.event


def jinja2_filters(project: Project) -> Filters:
    return {
        "person_timeline_events": lambda person: person_timeline_events(
            person, project.configuration.lifetime_threshold
        ),
        "person_descendant_families": person_descendant_families,
        "associated_file_references": associated_file_references,
    }


class ColorConfiguration(Configuration):
    """
    Configure a color.
    """

    _HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _assert_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise HumanFacingException(
                _(
                    '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.'
                ).format(
                    hex_value=hex_value,
                )
            )
        return hex_value

    @property
    def hex(self) -> str:
        """
        The color's hexadecimal value.
        """
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        self.assert_mutable()
        self._assert_hex(hex_value)
        self._hex = hex_value

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        self._hex = (assert_str() | self._assert_hex)(dump)

    @override
    def dump(self) -> Dump:
        return self._hex
