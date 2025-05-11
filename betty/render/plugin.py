"""
Integrate the render API with the plugin API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.render import Renderer as GenericRenderer

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class Renderer(GenericRenderer, Plugin):
    """
    A renderer plugin.
    """

    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return Renderer

    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "renderer"

    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Renderer")


RENDERER_REPOSITORY: PluginRepository[Renderer] = EntryPointPluginRepository(
    Renderer, "betty.renderer"
)
"""
The renderer plugin repository.

Read more about :doc:`/development/plugin/renderer`.
"""
