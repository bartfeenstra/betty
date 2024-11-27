"""
Integrate Betty with `Webpack <https://webpack.js.org/>`_.

This module is internal.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, Self, ClassVar

from typing_extensions import override

from betty import fs
from betty._npm import NpmRequirement, NpmUnavailable
from betty.html import CssProvider
from betty.jinja2 import Jinja2Provider, Filters, ContextVars
from betty.locale.localizable import _, Localizable, static
from betty.plugin import ShorthandPluginBase
from betty.project.extension import Extension
from betty.project.extension.webpack import build
from betty.project.extension.webpack.jinja2.filter import FILTERS
from betty.project.generate import GenerateSiteEvent
from betty.requirement import (
    Requirement,
    AllRequirements,
    AnyRequirement,
    RequirementError,
)
from betty.typing import internal, private

if TYPE_CHECKING:
    from betty.project import Project
    from betty.event_dispatcher import EventHandlerRegistry
    from collections.abc import Sequence


@internal
class PrebuiltAssetsRequirement(Requirement):
    """
    Check if prebuilt assets are available.
    """

    @override
    def is_met(self) -> bool:
        return (fs.PREBUILT_ASSETS_DIRECTORY_PATH / "webpack").is_dir()

    @override
    def summary(self) -> Localizable:
        return (
            _("Pre-built Webpack front-end assets are available")
            if self.is_met()
            else _("Pre-built Webpack front-end assets are unavailable")
        )


@internal
@final
class Webpack(ShorthandPluginBase, Extension, CssProvider, Jinja2Provider):
    """
    Integrate Betty with `Webpack <https://webpack.js.org/>`_.
    """

    _plugin_id = "webpack"
    _plugin_label = static("Webpack")
    _requirement: ClassVar[Requirement | None] = None

    @private
    def __init__(self, project: Project, public_css_paths: Sequence[str]):
        super().__init__(project)
        self._public_css_paths = public_css_paths

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        static_url_generator = await project.static_url_generator
        return cls(project, [static_url_generator.generate("/css/vendor.css")])

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, self._generate_assets)

    @override
    @classmethod
    async def requirement(cls) -> Requirement:
        if cls._requirement is None:
            cls._requirement = AllRequirements(
                await super().requirement(),
                AnyRequirement(await NpmRequirement.new(), PrebuiltAssetsRequirement()),
            )
        return cls._requirement

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    @property
    def public_css_paths(self) -> Sequence[str]:
        return self._public_css_paths

    @override
    def new_context_vars(self) -> ContextVars:
        return {
            "webpack_js_entry_points": set(),
        }

    @override
    @property
    def filters(self) -> Filters:
        return FILTERS

    async def _generate_assets(self, event: GenerateSiteEvent) -> None:
        builder = build.Builder(self._project)
        try:
            await builder.build(watch=event.watch)
        except NpmUnavailable:
            raise RequirementError(await self.requirement()) from None
