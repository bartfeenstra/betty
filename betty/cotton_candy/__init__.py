from __future__ import annotations

import logging
import re
from pathlib import Path
from shutil import copy2
from typing import Optional, Set, Type, Dict, Callable

from PyQt6.QtWidgets import QWidget
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app import Extension
from betty.app.extension import ConfigurableExtension, Theme
from betty.config import Configuration, DumpedConfiguration, VoidableDumpedConfiguration
from betty.config.dump import minimize
from betty.config.load import ConfigurationValidationError, Fields, Assertions, OptionalField, Asserter
from betty.cotton_candy.search import Index
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider
from betty.locale import Localizer
from betty.npm import _Npm, NpmBuilder, npm
from betty.project import EntityReferenceSequence

try:
    from typing_extensions import Self
except ModuleNotFoundError:
    from typing import Self  # type: ignore


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r'^#[a-zA-Z0-9]{6}$')

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _validate_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise ConfigurationValidationError(self.localizer._('"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.').format(hex_value=hex_value))
        return hex_value

    @property
    @reactive_property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        if hex_value is not None and not self._HEX_PATTERN.match(hex_value):
            raise ConfigurationValidationError(self.localizer._('"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.').format(hex_value=hex_value))
        self._hex = hex_value

    def update(self, other: Self) -> None:
        self.hex = other.hex

    @classmethod
    def load(
            cls,
            dumped_configuration: DumpedConfiguration,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        asserter = Asserter(localizer=localizer)
        hex_value = asserter.assert_str()(dumped_configuration)
        if configuration is None:
            configuration = cls(hex_value)
        else:
            configuration.hex = hex_value
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return self._hex


class CottonCandyConfiguration(Configuration):
    DEFAULT_PRIMARY_INACTIVE_COLOR = '#ffc0cb'
    DEFAULT_PRIMARY_ACTIVE_COLOR = '#ff69b4'
    DEFAULT_LINK_INACTIVE_COLOR = '#149988'
    DEFAULT_LINK_ACTIVE_COLOR = '#2a615a'

    def __init__(self):
        super().__init__()
        self._featured_entities = EntityReferenceSequence()
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
    def featured_entities(self) -> EntityReferenceSequence:
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
            dumped_configuration: DumpedConfiguration,
            configuration: Self | None = None,
            *,
            localizer: Localizer | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter(localizer=localizer)
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
        ))(dumped_configuration)
        return configuration

    def dump(self) -> VoidableDumpedConfiguration:
        return minimize({
            'featured_entities': self.featured_entities.dump(),
            'primary_inactive_color': self._primary_inactive_color.dump(),
            'primary_active_color': self._primary_active_color.dump(),
            'link_inactive_color': self._link_inactive_color.dump(),
            'link_active_color': self._link_active_color.dump(),
        })


class CottonCandy(Theme, ConfigurableExtension[CottonCandyConfiguration], Generator, GuiBuilder, ReactiveInstance, NpmBuilder, Jinja2Provider):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return 'Cotton Candy'

    @classmethod
    def default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._("Cotton Candy is Betty's default theme.")

    def gui_build(self) -> QWidget:
        from betty.cotton_candy.gui import _CottonCandyGuiWidget

        return _CottonCandyGuiWidget(self._app)

    @property
    def globals(self) -> Dict[str, Callable]:
        return {
            'search_index': lambda: Index(self.app).build(),
        }

    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        await self.app.extensions[_Npm].install(type(self), working_directory_path)
        await npm(('run', 'webpack'), cwd=working_directory_path)
        self._copy_npm_build(working_directory_path / 'webpack-build', assets_directory_path)
        logging.getLogger().info(self.app.localizer._('Built the Cotton Candy front-end assets.'))

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        destination_directory_path.mkdir(parents=True, exist_ok=True)
        copy2(source_directory_path / 'cotton_candy.css', destination_directory_path / 'cotton_candy.css')
        copy2(source_directory_path / 'cotton_candy.js', destination_directory_path / 'cotton_candy.js')

    async def generate(self) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self.app.static_www_directory_path)
