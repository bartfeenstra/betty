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
from betty.model.ancestry import File
from betty.npm import _Npm, NpmBuilder
from betty.project import EntityReference, EntityReferences

if TYPE_CHECKING:
    from betty.builtins import _


class CottonCandyConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self._background_image = EntityReference(entity_type_constraint=File)
        self._featured_entities = EntityReferences()
        self._featured_entities.react(self)

    @reactive  # type: ignore
    @property
    def background_image(self) -> EntityReference:
        return self._background_image

    @background_image.setter
    def background_image(self, background_image: EntityReference) -> None:
        self._background_image = background_image

    @property
    def featured_entities(self) -> EntityReferences:
        return self._featured_entities

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('The theme configuration must be a mapping (dictionary).'))

        if 'background_image_id' in dumped_configuration:
            with ensure_context('background_image_id'):
                self.background_image.load(dumped_configuration['background_image_id'])

        if 'featured_entities' in dumped_configuration:
            with ensure_context('featured_entities'):
                self.featured_entities.load(dumped_configuration['featured_entities'])

    def dump(self) -> DumpedConfiguration:
        return minimize_dumped_configuration({
            'background_image_id': self._background_image.dump(),
            'featured_entities': self.featured_entities.dump(),
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
        return _('Cotton Candy is a light theme featuring pastel colors')

    def gui_build(self) -> QWidget:
        from betty.cotton_candy.gui import _CottonCandyGuiWidget

        return _CottonCandyGuiWidget(self._app)

    @property
    def globals(self) -> Dict[str, Callable]:
        return {
            'search_index': lambda: Index(self.app).build(),
        }
