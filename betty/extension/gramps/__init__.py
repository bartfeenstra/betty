"""
Integrate Betty with `Gramps <https://gramps-project.org>`_.
"""

from __future__ import annotations

from typing import final

from typing_extensions import override

from betty.extension.gramps.config import GrampsConfiguration
from betty.gramps.loader import GrampsLoader
from betty.load import Loader
from betty.locale.localizable import plain, _, Localizable
from betty.project.extension import ConfigurableExtension
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.plugin import PluginId


@final
class Gramps(ConfigurableExtension[GrampsConfiguration], Loader):
    """
    Integrate Betty with `Gramps <https://gramps-project.org>`_.
    """

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return "gramps"

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
    def plugin_label(cls) -> Localizable:
        return plain("Gramps")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _('Load <a href="https://gramps-project.org/">Gramps</a> family trees.')
