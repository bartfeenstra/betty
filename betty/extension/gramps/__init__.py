"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.project.extension import ConfigurableExtension, UserFacingExtension
from betty.gramps.loader import GrampsLoader
from betty.locale import Str, Localizable

if TYPE_CHECKING:
    from betty.extension.gramps.gui import _GrampsGuiWidget

from betty.extension.gramps.config import GrampsConfiguration
from betty.gui import GuiBuilder
from betty.load import Loader


class Gramps(
    ConfigurableExtension[GrampsConfiguration], UserFacingExtension, Loader, GuiBuilder
):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    def name(cls) -> str:
        return "betty.extension.Gramps"

    @override
    @classmethod
    def default_configuration(cls) -> GrampsConfiguration:
        return GrampsConfiguration()

    @override
    async def load(self) -> None:
        for family_tree in self.configuration.family_trees:
            file_path = family_tree.file_path
            if file_path:
                await GrampsLoader(
                    self.project,
                    localizer=self.project.app.localizer,
                ).load_file(file_path)

    @override
    @classmethod
    def label(cls) -> Localizable:
        return Str.plain("Gramps")

    @override
    @classmethod
    def description(cls) -> Localizable:
        return Str._(
            'Load <a href="https://gramps-project.org/">Gramps</a> family trees.'
        )

    @override
    def gui_build(self) -> _GrampsGuiWidget:
        from betty.extension.gramps.gui import _GrampsGuiWidget

        return _GrampsGuiWidget(self._project)
