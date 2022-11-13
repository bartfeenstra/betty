import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING, Set, Type, Dict, Callable

from PyQt6.QtWidgets import QWidget
from reactives import reactive
from reactives.factory.type import ReactiveInstance

from betty.app import Extension
from betty.app.extension import ConfigurableExtension, Theme
from betty.config import Configuration, ConfigurationError, DumpedConfiguration, minimize_dumped_configuration
from betty.cotton_candy.search import Index
from betty.error import ensure_context
from betty.gui import GuiBuilder
from betty.jinja2 import Jinja2Provider
from betty.npm import _Npm, NpmBuilder
from betty.project import EntityReferences

if TYPE_CHECKING:
    from betty.builtins import _


class _ColorConfiguration(Configuration):
    _HEX_PATTERN = re.compile(r'^#[a-zA-Z0-9]{6}$')

    def __init__(self, hex_value: str):
        super().__init__()
        self._hex: str
        self.hex = hex_value

    @reactive  # type: ignore
    @property
    def hex(self) -> str:
        return self._hex

    @hex.setter
    def hex(self, hex_value: str) -> None:
        if hex_value is None:
            self._hex = None
            return

        if not self._HEX_PATTERN.match(hex_value):
            raise ConfigurationError(_('"{hex_value}" is not a valid hexadecimal color, such as #ffc0cb.').format(hex_value=hex_value))

        self._hex = hex_value

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, str):
            raise ConfigurationError(_('Color configuration must be a string.'))
        self.hex = dumped_configuration

    def dump(self) -> DumpedConfiguration:
        return self._hex


class CottonCandyConfiguration(Configuration):
    DEFAULT_PRIMARY_INACTIVE_COLOR = '#ffc0cb'
    DEFAULT_PRIMARY_ACTIVE_COLOR = '#ff69b4'
    DEFAULT_LINK_INACTIVE_COLOR = '#149988'
    DEFAULT_LINK_ACTIVE_COLOR = '#2a615a'

    def __init__(self):
        super().__init__()
        self._featured_entities = EntityReferences()
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
    def featured_entities(self) -> EntityReferences:
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

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('The theme configuration must be a mapping (dictionary).'))

        if 'featured_entities' in dumped_configuration:
            with ensure_context('featured_entities'):
                self._featured_entities.load(dumped_configuration['featured_entities'])

        if 'primary_inactive_color' in dumped_configuration:
            with ensure_context('primary_inactive_color'):
                self._primary_inactive_color.load(dumped_configuration['primary_inactive_color'])

        if 'primary_active_color' in dumped_configuration:
            with ensure_context('primary_active_color'):
                self._primary_active_color.load(dumped_configuration['primary_active_color'])

        if 'link_inactive_color' in dumped_configuration:
            with ensure_context('link_inactive_color'):
                self._link_inactive_color.load(dumped_configuration['link_inactive_color'])

        if 'link_active_color' in dumped_configuration:
            with ensure_context('link_active_color'):
                self._link_active_color.load(dumped_configuration['link_active_color'])

    def dump(self) -> DumpedConfiguration:
        return minimize_dumped_configuration({
            'featured_entities': self.featured_entities.dump(),
            'primary_inactive_color': self._primary_inactive_color.dump(),
            'primary_active_color': self._primary_active_color.dump(),
            'link_inactive_color': self._link_inactive_color.dump(),
            'link_active_color': self._link_active_color.dump(),
        })


@reactive
class CottonCandy(Theme, ConfigurableExtension[CottonCandyConfiguration], GuiBuilder, ReactiveInstance, NpmBuilder, Jinja2Provider):
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
