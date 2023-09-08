from __future__ import annotations

from typing import TYPE_CHECKING

from betty.app.extension import ConfigurableExtension, UserFacingExtension
from betty.gramps.loader import GrampsLoader
from betty.locale import Str

if TYPE_CHECKING:
    from betty.extension.gramps.gui import _GrampsGuiWidget

from betty.extension.gramps.config import GrampsConfiguration
from betty.gui import GuiBuilder
from betty.load import Loader


class _Gramps(ConfigurableExtension[GrampsConfiguration], UserFacingExtension, Loader, GuiBuilder):
    @classmethod
    def default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    async def load(self) -> None:
        for family_tree in self.configuration.family_trees:
            file_path = family_tree.file_path
            if file_path:
                await GrampsLoader(
                    self._app.project.ancestry,
                    localizer=self._app.localizer,
                ).load_file(file_path)

    @classmethod
    def label(cls) -> Str:
        return Str.plain('Gramps')

    @classmethod
    def description(cls) -> Str:
        return Str._('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')

    def gui_build(self) -> _GrampsGuiWidget:
        from betty.extension.gramps.gui import _GrampsGuiWidget

        return _GrampsGuiWidget(self._app)
