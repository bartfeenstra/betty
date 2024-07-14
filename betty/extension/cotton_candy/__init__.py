"""
Provide Betty's default theme.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Self, cast, TYPE_CHECKING, final

from jinja2 import pass_context
from typing_extensions import override

from betty import fs
from betty.assertion import (
    OptionalField,
    assert_str,
    assert_record,
    assert_path,
    assert_setattr,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.extension.cotton_candy.search import Index
from betty.extension.maps import Maps
from betty.extension.trees import Trees
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.functools import Uniquifier
from betty.generate import GenerateSiteEvent
from betty.html import CssProvider
from betty.jinja2 import (
    Jinja2Provider,
    context_project,
    context_localizer,
    context_job_context,
    Globals,
    Filters,
)
from betty.locale.date import Date, Datey
from betty.locale.localizable import _, plain, Localizable
from betty.model import Entity, UserFacingEntity, GeneratedEntityId
from betty.model.ancestry import (
    Event,
    Person,
    Presence,
    is_public,
    HasFileReferences,
    Place,
    FileReference,
)
from betty.model.event_type import StartOfLifeEventType, EndOfLifeEventType
from betty.model.presence_role import Subject
from betty.os import link_or_copy
from betty.project import EntityReferenceSequence, EntityReference
from betty.project.extension import ConfigurableExtension, Theme
from betty.serde.dump import minimize, Dump, VoidableDump
from betty.typing import Void

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginId
    from jinja2.runtime import Context
    from collections.abc import Sequence, AsyncIterable


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _assert_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(
                _(
                    '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.'
                ).format(
                    hex_value=hex_value,
                )
            )
        return hex_value

    @property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        self._assert_hex(hex_value)
        self._hex = hex_value

    @override
    def update(self, other: Self) -> None:
        self.hex = other.hex

    @override
    def load(self, dump: Dump) -> None:
        self._hex = (assert_str() | self._assert_hex)(dump)

    @override
    def dump(self) -> VoidableDump:
        return self._hex


class CottonCandyConfiguration(Configuration):
    """
    Provide configuration for the :py:class:`betty.extension.cotton_candy.CottonCandy` extension.
    """

    DEFAULT_PRIMARY_INACTIVE_COLOR = "#ffc0cb"
    DEFAULT_PRIMARY_ACTIVE_COLOR = "#ff69b4"
    DEFAULT_LINK_INACTIVE_COLOR = "#149988"
    DEFAULT_LINK_ACTIVE_COLOR = "#2a615a"

    def __init__(
        self,
        *,
        featured_entities: (
            Sequence[EntityReference[UserFacingEntity & Entity]] | None
        ) = None,
        primary_inactive_color: str = DEFAULT_PRIMARY_INACTIVE_COLOR,
        primary_active_color: str = DEFAULT_PRIMARY_ACTIVE_COLOR,
        link_inactive_color: str = DEFAULT_LINK_INACTIVE_COLOR,
        link_active_color: str = DEFAULT_LINK_ACTIVE_COLOR,
        logo: Path | None = None,
    ):
        super().__init__()
        self._featured_entities = EntityReferenceSequence["UserFacingEntity & Entity"](
            featured_entities or ()
        )
        self._primary_inactive_color = _ColorConfiguration(primary_inactive_color)
        self._primary_active_color = _ColorConfiguration(primary_active_color)
        self._link_inactive_color = _ColorConfiguration(link_inactive_color)
        self._link_active_color = _ColorConfiguration(link_active_color)
        self._logo = logo

    @property
    def featured_entities(self) -> EntityReferenceSequence[UserFacingEntity & Entity]:
        """
        The entities featured on the front page.
        """
        return self._featured_entities

    @property
    def primary_inactive_color(self) -> _ColorConfiguration:
        """
        The color for inactive primary/CTA elements.
        """
        return self._primary_inactive_color

    @property
    def primary_active_color(self) -> _ColorConfiguration:
        """
        The color for active primary/CTA elements.
        """
        return self._primary_active_color

    @property
    def link_inactive_color(self) -> _ColorConfiguration:
        """
        The color for inactive hyperlinks.
        """
        return self._link_inactive_color

    @property
    def link_active_color(self) -> _ColorConfiguration:
        """
        The color for active hyperlinks.
        """
        return self._link_active_color

    @property
    def logo(self) -> Path | None:
        """
        The path to the logo.
        """
        return self._logo

    @logo.setter
    def logo(self, logo: Path | None) -> None:
        self._logo = logo

    @override
    def update(self, other: Self) -> None:
        self.featured_entities.update(other.featured_entities)
        self.primary_inactive_color.update(other.primary_inactive_color)
        self.primary_active_color.update(other.primary_active_color)
        self.link_inactive_color.update(other.link_inactive_color)
        self.link_active_color.update(other.link_active_color)
        self.logo = other.logo

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("featured_entities", self.featured_entities.load),
            OptionalField("primary_inactive_color", self.primary_inactive_color.load),
            OptionalField("primary_active_color", self.primary_active_color.load),
            OptionalField("link_inactive_color", self.link_inactive_color.load),
            OptionalField("link_active_color", self.link_active_color.load),
            OptionalField("logo", assert_path() | assert_setattr(self, "logo")),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "featured_entities": self.featured_entities.dump(),
                "primary_inactive_color": self._primary_inactive_color.dump(),
                "primary_active_color": self._primary_active_color.dump(),
                "link_inactive_color": self._link_inactive_color.dump(),
                "link_active_color": self._link_active_color.dump(),
                "logo": str(self._logo) if self._logo else Void,
            }
        )


async def _generate_favicon(event: GenerateSiteEvent) -> None:
    cotton_candy = event.project.extensions[CottonCandy.plugin_id()]
    assert isinstance(cotton_candy, CottonCandy)
    await link_or_copy(
        cotton_candy.logo, event.project.configuration.www_directory_path / "logo.png"
    )


@final
class CottonCandy(
    Theme,
    CssProvider,
    ConfigurableExtension[CottonCandyConfiguration],
    Jinja2Provider,
    WebpackEntryPointProvider,
):
    """
    Provide Betty's default front-end theme.
    """

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return "cotton-candy"

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_favicon)

    @override
    @classmethod
    def depends_on(cls) -> set[PluginId]:
        return {Webpack.plugin_id()}

    @override
    @classmethod
    def comes_after(cls) -> set[PluginId]:
        return {Maps.plugin_id(), Trees.plugin_id()}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self.project.configuration.root_path,
            self._configuration.primary_inactive_color.hex,
            self._configuration.primary_active_color.hex,
            self._configuration.link_inactive_color.hex,
            self._configuration.link_active_color.hex,
        )

    @override
    @property
    def public_css_paths(self) -> list[str]:
        return [
            self.project.static_url_generator.generate("css/cotton-candy.css"),
        ]

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("Cotton Candy")

    @override
    @classmethod
    def default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _("Cotton Candy is Betty's default theme.")

    @property
    def logo(self) -> Path:
        """
        The path to the logo file.
        """
        return (
            self._configuration.logo
            or fs.ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png"
        )

    @override
    @property
    def globals(self) -> Globals:
        return {
            "search_index": _global_search_index,
        }

    @override
    @property
    def filters(self) -> Filters:
        return {
            "person_timeline_events": lambda person: person_timeline_events(
                person, self.project.configuration.lifetime_threshold
            ),
            "person_descendant_families": person_descendant_families,
            "associated_file_references": associated_file_references,
        }


@pass_context
async def _global_search_index(context: Context) -> AsyncIterable[dict[str, str]]:
    return Index(
        context_project(context),
        context_job_context(context),
        context_localizer(context),
    ).build()


def _is_person_timeline_presence(presence: Presence) -> bool:
    if presence.private:
        return False
    if not presence.event:
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
    yield from Uniquifier(_person_timeline_events(person, lifetime_threshold))


def person_descendant_families(
    person: Person,
) -> Iterable[tuple[Sequence[Person], Sequence[Person]]]:
    """
    Gather a person's families they are a parent in.
    """
    parents = {}
    children = defaultdict(set)
    for child in person.children:
        family = tuple(sorted((parent.id for parent in child.parents)))
        if family not in parents:
            parents[family] = tuple(child.parents)
        children[family].add(child)
    yield from zip(parents.values(), children.values())


def associated_file_references(
    has_file_references: HasFileReferences,
) -> Iterable[FileReference]:
    """
    Get the associated file references for an entity that has file references.
    """
    yield from Uniquifier(
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
            if presence.event is not None:
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
        if not isinstance(presence.role, Subject):
            continue
        if issubclass(presence.event.event_type, StartOfLifeEventType):
            start_dates.append(presence.event.date)
        if issubclass(presence.event.event_type, EndOfLifeEventType):
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
            cast(Datey, cast(Event, presence.event).date)
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
                if not associated_presence.event or not issubclass(
                    associated_presence.event.event_type,
                    (StartOfLifeEventType, EndOfLifeEventType),
                ):
                    continue
                if isinstance(associated_presence.event.id, GeneratedEntityId):
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
