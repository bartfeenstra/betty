from __future__ import annotations

import logging
import re
from pathlib import Path
from shutil import copy2
from typing import Any, Callable, Iterable, cast, Self

from PyQt6.QtWidgets import QWidget
from aiofiles.os import makedirs
from jinja2 import pass_context
from jinja2.runtime import Context
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app.extension import ConfigurableExtension, Extension, Theme
from betty.config import Configuration
from betty.extension.cotton_candy.search import Index
from betty.extension.npm import _Npm, NpmBuilder, npm
from betty.functools import walk
from betty.generate import Generator, GenerationContext
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider, context_app, context_localizer, context_task_context
from betty.locale import Date, Datey, Str
from betty.model import Entity, UserFacingEntity
from betty.model.ancestry import Event, Person, Presence, is_public
from betty.project import EntityReferenceSequence
from betty.serde.dump import minimize, Dump, VoidableDump
from betty.serde.load import AssertionFailed, Fields, Assertions, OptionalField, Asserter


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r'^#[a-zA-Z0-9]{6}$')

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _validate_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(Str._(
                '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.',
                hex_value=hex_value,
            ))
        return hex_value

    @property
    @reactive_property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        if not self._HEX_PATTERN.match(hex_value):
            raise AssertionFailed(Str._(
                '"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.',
                hex_value=hex_value,
            ))
        self._hex = hex_value

    def update(self, other: Self) -> None:
        self.hex = other.hex

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        asserter = Asserter()
        hex_value = asserter.assert_str()(dump)
        if configuration is None:
            configuration = cls(hex_value)
        else:
            configuration.hex = hex_value
        return configuration

    def dump(self) -> VoidableDump:
        return self._hex


class CottonCandyConfiguration(Configuration):
    DEFAULT_PRIMARY_INACTIVE_COLOR = '#ffc0cb'
    DEFAULT_PRIMARY_ACTIVE_COLOR = '#ff69b4'
    DEFAULT_LINK_INACTIVE_COLOR = '#149988'
    DEFAULT_LINK_ACTIVE_COLOR = '#2a615a'

    def __init__(self):
        super().__init__()
        self._featured_entities = EntityReferenceSequence['UserFacingEntity & Entity']()
        self._featured_entities.react(self)
        self._primary_inactive_color = _ColorConfiguration(self.DEFAULT_PRIMARY_INACTIVE_COLOR)
        self._primary_inactive_color.react(self)
        self._primary_active_color = _ColorConfiguration(self.DEFAULT_PRIMARY_ACTIVE_COLOR)
        self._primary_active_color.react(self)
        self._link_inactive_color = _ColorConfiguration(self.DEFAULT_LINK_INACTIVE_COLOR)
        self._link_inactive_color.react(self)
        self._link_active_color = _ColorConfiguration(self.DEFAULT_LINK_ACTIVE_COLOR)
        self._link_active_color.react(self)

    @property
    def featured_entities(self) -> EntityReferenceSequence[UserFacingEntity & Entity]:
        return self._featured_entities

    @property
    def primary_inactive_color(self) -> _ColorConfiguration:
        return self._primary_inactive_color

    @property
    def primary_active_color(self) -> _ColorConfiguration:
        return self._primary_active_color

    @property
    def link_inactive_color(self) -> _ColorConfiguration:
        return self._link_inactive_color

    @property
    def link_active_color(self) -> _ColorConfiguration:
        return self._link_active_color

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(Fields(
            OptionalField(
                'featured_entities',
                Assertions(configuration._featured_entities.assert_load(configuration._featured_entities)),
            ),
            OptionalField(
                'primary_inactive_color',
                Assertions(configuration._primary_inactive_color.assert_load(configuration._primary_inactive_color)),
            ),
            OptionalField(
                'primary_active_color',
                Assertions(configuration._primary_active_color.assert_load(configuration._primary_active_color)),
            ),
            OptionalField(
                'link_inactive_color',
                Assertions(configuration._link_inactive_color.assert_load(configuration._link_inactive_color)),
            ),
            OptionalField(
                'link_active_color',
                Assertions(configuration._link_active_color.assert_load(configuration._link_active_color)),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDump:
        return minimize({
            'featured_entities': self.featured_entities.dump(),
            'primary_inactive_color': self._primary_inactive_color.dump(),
            'primary_active_color': self._primary_active_color.dump(),
            'link_inactive_color': self._link_inactive_color.dump(),
            'link_active_color': self._link_active_color.dump(),
        })


class _CottonCandy(Theme, ConfigurableExtension[CottonCandyConfiguration], Generator, GuiBuilder, ReactiveInstance, NpmBuilder, Jinja2Provider):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Npm}

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> Str:
        return Str.plain('Cotton Candy')

    @classmethod
    def default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @classmethod
    def description(cls) -> Str:
        return Str._("Cotton Candy is Betty's default theme.")

    def gui_build(self) -> QWidget:
        from betty.extension.cotton_candy.gui import _CottonCandyGuiWidget

        return _CottonCandyGuiWidget(self._app)

    @property
    def globals(self) -> dict[str, Any]:
        return {
            'search_index': _global_search_index,
        }

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return {
            'person_timeline_events': lambda person: person_timeline_events(
                person,
                self.app.project.configuration.lifetime_threshold
            ),
        }

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path)
        await self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info(self._app.localizer._('Built the Cotton Candy front-end assets.'))

    async def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        await makedirs(destination_directory_path, exist_ok=True)
        copy2(source_directory_path / 'cotton_candy.css', destination_directory_path / 'cotton_candy.css')
        copy2(source_directory_path / 'cotton_candy.js', destination_directory_path / 'cotton_candy.js')

    async def generate(self, task_context: GenerationContext) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        await self._copy_npm_build(assets_directory_path, self.app.project.configuration.www_directory_path)


@pass_context
async def _global_search_index(context: Context) -> Iterable[dict[str, str]]:
    return await Index(
        context_app(context),
        context_task_context(context),
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
    # Collect all associated events for a person.
    # Start with the person's own events for which their presence is public.
    for presence in person.presences:
        if _is_person_timeline_presence(presence):
            yield cast(Event, presence.event)
        continue

    # If the person has start- or end-of-life events, we use those to constrain associated people's events.
    start_date = None
    end_date = None
    if person.start and _is_person_timeline_presence(person.start):
        start_date = cast(Event, person.start.event).date
    if person.end and _is_person_timeline_presence(person.end):
        end_date = cast(Event, person.end.event).date

    # If an end-of-life event exists, but no start-of-life event, create a start-of-life date based on the end date,
    # minus the lifetime threshold.
    if not start_date and end_date:
        if isinstance(end_date, Date):
            start_date_reference = end_date
        else:
            if end_date.end and end_date.end.comparable:
                start_date_reference = end_date.end
            else:
                start_date_reference = cast(Date, end_date.start)
        start_date = Date(
            cast(int, start_date_reference.year) - lifetime_threshold,
            start_date_reference.month,
            start_date_reference.day,
            start_date_reference.fuzzy,
        )

    # If a start-of-life event exists, but no end-of-life event, create an end-of-life date based on the start date,
    # plus the lifetime threshold.
    if not end_date and start_date:
        if isinstance(start_date, Date):
            end_date_reference = start_date
        else:
            if start_date.start and start_date.start.comparable:
                end_date_reference = start_date.start
            else:
                end_date_reference = cast(Date, start_date.end)
        end_date = Date(
            cast(int, end_date_reference.year) + lifetime_threshold,
            end_date_reference.month,
            end_date_reference.day,
            end_date_reference.fuzzy,
        )

    if not start_date or not end_date:
        reference_dates = list(sorted(
            cast(Datey, cast(Event, presence.event).date)
            for presence
            in person.presences
            if _is_person_timeline_presence(presence)
        ))
        if reference_dates:
            if not start_date:
                start_date = reference_dates[0]
            if not end_date:
                end_date = reference_dates[-1]

    if start_date and end_date:
        associated_people = filter(is_public, (
            # All ancestors.
            *walk(person, 'parents'),
            # All descendants.
            *walk(person, 'children'),
            # All siblings.
            *person.siblings,
        ))
        for associated_person in associated_people:
            # For associated events, we are only interested in people's start- or end-of-life events.
            for associated_presence in (associated_person.start, associated_person.end):
                if associated_presence is None:
                    continue
                if not _is_person_timeline_presence(associated_presence):
                    continue
                if cast(Event, associated_presence.event).date < start_date:
                    continue
                if cast(Event, associated_presence.event).date > end_date:
                    continue
                yield cast(Event, associated_presence.event)
