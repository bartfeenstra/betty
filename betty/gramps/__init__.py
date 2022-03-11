from typing import Optional, Type

from PyQt6.QtWidgets import QWidget

from betty.app import Extension
from betty.config import Configuration, Configurable
from betty.gramps.config import GrampsConfiguration
from betty.gramps.gui import _GrampsGuiWidget
from betty.gramps.loader import load_file
from betty.gui import GuiBuilder
from betty.load import Loader


class Gramps(Extension, Configurable, Loader, GuiBuilder):
    @classmethod
    def configuration_type(cls) -> Type[Configuration]:
        return GrampsConfiguration

    async def load(self) -> None:
        for family_tree in self._configuration.family_trees:
            await load_file(self._app.ancestry, family_tree.file_path)

    @classmethod
    def label(cls) -> str:
        return 'Gramps'

    @classmethod
    def gui_description(cls) -> str:
        return _('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')

    def gui_build(self) -> Optional[QWidget]:
        return _GrampsGuiWidget(self._configuration)
