"""Integrate Betty with `Leaflet.js <https://leafletjs.com/>`_."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.html import CssProvider
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.typing import private

if TYPE_CHECKING:
    from betty.project import Project
    from betty.project.extension import Extension
    from betty.plugin import PluginIdentifier
    from collections.abc import Sequence


@final
class Maps(ShorthandPluginBase, CssProvider, EntryPointProvider):
    """
    Provide interactive maps for use on web pages.
    """

    _plugin_id = "maps"
    _plugin_label = _("Maps")
    _plugin_description = _(
        'Display lists of places as interactive maps using <a href="https://leafletjs.com/">Leaflet</a>.'
    )

    @private
    def __init__(self, project: Project, _public_css_paths: Sequence[str]):
        super().__init__(project)
        self._public_css_paths = _public_css_paths

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        url_generator = await project.url_generator
        return cls(
            project,
            [url_generator.generate(f"betty-static:///css/{cls.plugin_id()}.css")],
        )

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return ()

    @override
    @property
    def public_css_paths(self) -> Sequence[str]:
        return self._public_css_paths
