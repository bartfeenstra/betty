"""
Provide the Cotton Candy theme.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.html import CssProvider
from betty.jinja2 import Jinja2Provider, Filters
from betty.locale.localizable import _, static, plain
from betty.os import link_or_copy
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension, Theme, Extension
from betty.project.extension._theme import jinja2_filters
from betty.project.extension._theme.search import generate_search_index
from betty.project.extension.cotton_candy.config import CottonCandyConfiguration
from betty.project.extension.maps import Maps
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import GenerateSiteEvent
from betty.typing import private

if TYPE_CHECKING:
    from betty.project import Project
    from betty.plugin import PluginIdentifier
    from betty.event_dispatcher import EventHandlerRegistry
    from collections.abc import Sequence

_RESULT_CONTAINER_TEMPLATE = plain("""
<li class="search-result">
    {{{ betty-search-result }}}
</li>
""")

_RESULTS_CONTAINER_TEMPLATE = plain("""
<ul id="search-results" class="nav-secondary">
    {{{ betty-search-results }}}
</ul>
""")


async def _generate_logo(event: GenerateSiteEvent) -> None:
    await link_or_copy(
        event.project.logo, event.project.configuration.www_directory_path / "logo.png"
    )


async def _generate_search_index(event: GenerateSiteEvent) -> None:
    await generate_search_index(
        event.project,
        _RESULT_CONTAINER_TEMPLATE,
        _RESULTS_CONTAINER_TEMPLATE,
        job_context=event.job_context,
    )


@final
class CottonCandy(
    ShorthandPluginBase,
    Theme,
    CssProvider,
    ConfigurableExtension[CottonCandyConfiguration],
    Jinja2Provider,
    EntryPointProvider,
):
    """
    The Cotton Candy theme.
    """

    _plugin_id = "cotton-candy"
    _plugin_label = static("Cotton Candy")
    _plugin_description = _("Cotton Candy is Betty's default theme.")

    @private
    def __init__(
        self,
        project: Project,
        public_css_paths: Sequence[str],
        *,
        configuration: CottonCandyConfiguration,
    ):
        super().__init__(project, configuration=configuration)
        self._public_css_paths = public_css_paths

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        static_url_generator = await project.static_url_generator
        return cls(
            project,
            [static_url_generator.generate("/css/cotton-candy.css")],
            configuration=cls.new_default_configuration(),
        )

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        try:
            await self._assert_configuration()
        except BaseException:
            await self.shutdown()
            raise

    async def _assert_configuration(self) -> None:
        await self.configuration.featured_entities.validate(
            self.project.entity_type_repository
        )

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(GenerateSiteEvent, _generate_logo, _generate_search_index)

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {Webpack}

    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {Maps, Trees}

    @override
    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / "assets"

    @override
    @classmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        return Path(__file__).parent / "webpack"

    @override
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        return (
            self.project.configuration.root_path,
            self._configuration.primary_inactive_color.hex,
            self._configuration.primary_active_color.hex,
            self._configuration.link_inactive_color.hex,
            self._configuration.link_active_color.hex,
        )

    @override
    @property
    def public_css_paths(self) -> Sequence[str]:
        return self._public_css_paths

    @override
    @classmethod
    def new_default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self._project)
