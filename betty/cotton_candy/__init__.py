import logging
import re
from pathlib import Path
from shutil import copy2
from typing import Optional, TYPE_CHECKING, Set, Type, Dict, Callable

from PyQt6.QtWidgets import QWidget
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.app import Extension
from betty.app.extension import ConfigurableExtension, Theme
from betty.config import Configuration, DumpedConfigurationImport, DumpedConfigurationExport
from betty.config.dump import minimize_dict
from betty.config.load import ConfigurationValidationError, Loader, Field
from betty.cotton_candy.search import Index
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider
from betty.npm import _Npm, NpmBuilder, npm
from betty.project import EntityReferenceCollection

if TYPE_CHECKING:
    from betty.builtins import _


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r'^#[a-zA-Z0-9]{6}$')

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    def _validate_hex(self, hex_value: str) -> str:
        if not self._HEX_PATTERN.match(hex_value):
            raise ConfigurationValidationError(_('"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.').format(hex_value=hex_value))
        return hex_value

    @property
    @reactive_property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        self._validate_hex(hex_value)
        self._hex = hex_value

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        if loader.assert_str(dumped_configuration):
            loader.assert_setattr(self, 'hex', dumped_configuration)

    def dump(self) -> DumpedConfigurationExport:
        return self._hex


class CottonCandyConfiguration(Configuration):
    DEFAULT_PRIMARY_INACTIVE_COLOR = '#ffc0cb'
    DEFAULT_PRIMARY_ACTIVE_COLOR = '#ff69b4'
    DEFAULT_LINK_INACTIVE_COLOR = '#149988'
    DEFAULT_LINK_ACTIVE_COLOR = '#2a615a'

    def __init__(self):
        super().__init__()
        self._featured_entities = EntityReferenceCollection()
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
    def featured_entities(self) -> EntityReferenceCollection:
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

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'featured_entities': Field(
                False,
                self._featured_entities.load,  # type: ignore
            ),
            'primary_inactive_color': Field(
                False,
                self._primary_inactive_color.load,  # type: ignore
            ),
            'primary_active_color': Field(
                False,
                self._primary_active_color.load,  # type: ignore
            ),
            'link_inactive_color': Field(
                False,
                self._link_inactive_color.load,  # type: ignore
            ),
            'link_active_color': Field(
                False,
                self._link_active_color.load,  # type: ignore
            ),
        })

    def dump(self) -> DumpedConfigurationExport:
        return minimize_dict({
            'featured_entities': self.featured_entities.dump(),
            'primary_inactive_color': self._primary_inactive_color.dump(),
            'primary_active_color': self._primary_active_color.dump(),
            'link_inactive_color': self._link_inactive_color.dump(),
            'link_active_color': self._link_active_color.dump(),
        }, True)


class CottonCandy(Theme, ConfigurableExtension[CottonCandyConfiguration], Generator, GuiBuilder, ReactiveInstance, NpmBuilder, Jinja2Provider):
    @classmethod
    def depends_on(cls) -> Set[Type[Extension]]:
        return {_Npm}

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @classmethod
    def label(cls) -> str:
        return 'Cotton Candy'

    @classmethod
    def default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @classmethod
    def description(cls) -> str:
        return _("Cotton Candy is Betty's default theme.")

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
        logging.getLogger().info('Built the Cotton Candy front-end assets.')

    def _copy_npm_build(self, source_directory_path: Path, destination_directory_path: Path) -> None:
        copy2(source_directory_path / 'cotton_candy.css', destination_directory_path / 'cotton_candy.css')
        copy2(source_directory_path / 'cotton_candy.js', destination_directory_path / 'cotton_candy.js')

    async def generate(self) -> None:
        assets_directory_path = await self.app.extensions[_Npm].ensure_assets(self)
        self._copy_npm_build(assets_directory_path, self.app.project.configuration.www_directory_path)
