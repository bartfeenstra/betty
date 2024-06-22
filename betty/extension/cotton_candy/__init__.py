"""
Provide Betty's default theme.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Self, cast, TYPE_CHECKING

from jinja2 import pass_context
from typing_extensions import override

from betty import fs
from betty.app.extension import ConfigurableExtension, Extension, Theme
from betty.config import Configuration
from betty.extension.cotton_candy.search import Index
from betty.extension.webpack import Webpack, WebpackEntryPointProvider
from betty.functools import Uniquifier
from betty.generate import Generator, GenerationContext
from betty.gui import GuiBuilder
from betty.html import CssProvider
from betty.jinja2 import (
    Jinja2Provider,
    context_app,
    context_localizer,
    context_job_context,
    Globals,
    Filters,
)
from betty.locale import Date, Str, Datey, Localizable
from betty.model import Entity, UserFacingEntity, GeneratedEntityId
from betty.model.ancestry import Event, Person, Presence, is_public, Subject
from betty.model.event_type import StartOfLifeEventType, EndOfLifeEventType
from betty.os import link_or_copy
from betty.project import EntityReferenceSequence, EntityReference
from betty.serde.dump import minimize, Dump, VoidableDump, Void
from betty.serde.load import (
    AssertionFailed,
    OptionalField,
    AssertionChain,
    assert_str,
    assert_record,
    assert_path,
    assert_setattr,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    from jinja2.runtime import Context
    from collections.abc import Sequence, AsyncIterable


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r"^#[a-zA-Z0-9]{6}$")

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _validate_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(
                Str._(
                    '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.',
                    hex_value=hex_value,
                )
            )
        return hex_value

    @property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(
                Str._(
                    '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.',
                    hex_value=hex_value,
                )
            )
        self._hex = hex_value
        self._dispatch_change()

    @override
    def update(self, other: Self) -> None:
        self.hex = other.hex

    @override
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        hex_value = assert_str()(dump)
        if configuration is None:
            configuration = cls(hex_value)
        else:
            configuration.hex = hex_value
        return configuration

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
        self._featured_entities.on_change(self)
        self._primary_inactive_color = _ColorConfiguration(primary_inactive_color)
        self._primary_inactive_color.on_change(self)
        self._primary_active_color = _ColorConfiguration(primary_active_color)
        self._primary_active_color.on_change(self)
        self._link_inactive_color = _ColorConfiguration(link_inactive_color)
        self._link_inactive_color.on_change(self)
        self._link_active_color = _ColorConfiguration(link_active_color)
        self._link_active_color.on_change(self)
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
        self._dispatch_change()

    @override
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        assert_record(
            OptionalField(
                "featured_entities",
                configuration._featured_entities.assert_load(
                    configuration._featured_entities
                ),
            ),
            OptionalField(
                "primary_inactive_color",
                configuration._primary_inactive_color.assert_load(
                    configuration._primary_inactive_color
                ),
            ),
            OptionalField(
                "primary_active_color",
                configuration._primary_active_color.assert_load(
                    configuration._primary_active_color
                ),
            ),
            OptionalField(
                "link_inactive_color",
                configuration._link_inactive_color.assert_load(
                    configuration._link_inactive_color
                ),
            ),
            OptionalField(
                "link_active_color",
                configuration._link_active_color.assert_load(
                    configuration._link_active_color
                ),
            ),
            OptionalField(
                "logo",
                AssertionChain(assert_path()) | assert_setattr(configuration, "logo"),
            ),
        )(dump)
        return configuration

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


class CottonCandy(
    Theme,
    CssProvider,
    ConfigurableExtension[CottonCandyConfiguration],
    Generator,
    GuiBuilder,
    Jinja2Provider,
    WebpackEntryPointProvider,
):
    """
    Provide Betty's default front-end theme.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.CottonCandy"

    @override
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        from betty.extension import Maps, Trees

        return {Maps, Trees}

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
            self._app.project.configuration.root_path,
            self._configuration.primary_inactive_color.hex,
            self._configuration.primary_active_color.hex,
            self._configuration.link_inactive_color.hex,
            self._configuration.link_active_color.hex,
        )

    @override
    @property
    def public_css_paths(self) -> list[str]:
        return [
            self.app.static_url_generator.generate(
                "css/betty.extension.CottonCandy.css"
            ),
        ]

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str.plain("Cotton Candy")

    @override
    @classmethod
    def default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._("Cotton Candy is Betty's default theme.")

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
    async def generate(self, job_context: GenerationContext) -> None:
        await link_or_copy(
            self.logo, self._app.project.configuration.www_directory_path / "logo.png"
        )

    @override
    def gui_build(self) -> QWidget:
        from betty.extension.cotton_candy.gui import _CottonCandyGuiWidget

        return _CottonCandyGuiWidget(self._app)

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
                person, self.app.project.configuration.lifetime_threshold
            ),
            "person_descendant_families": person_descendant_families,
        }


@pass_context
async def _global_search_index(context: Context) -> AsyncIterable[dict[str, str]]:
    return Index(
        context_app(context),
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
