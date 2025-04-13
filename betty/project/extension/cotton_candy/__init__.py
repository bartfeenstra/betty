"""
Provide the Cotton Candy theme.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, final

from typing_extensions import deprecated, override

from betty.jinja2 import Filters, Jinja2Provider
from betty.locale.localizable import _, plain, static
from betty.os import link_or_copy
from betty.plugin import ShorthandPluginBase
from betty.project.extension import ConfigurableExtension, Extension, Theme
from betty.project.extension._theme import jinja2_filters
from betty.project.extension._theme.search import generate_search_index
from betty.project.extension.cotton_candy.config import CottonCandyConfiguration
from betty.project.extension.maps import Maps
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import GenerateSiteEvent

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.plugin import PluginIdentifier

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
@deprecated(
    "The Cotton Candy theme has been deprecated since Betty 0.4.9, and will be removed in Betty 0.5. Instead use Raspberry Mint (`raspberry-mint`)."
)
class CottonCandy(
    ShorthandPluginBase,
    Theme,
    ConfigurableExtension[CottonCandyConfiguration],
    Jinja2Provider,
    EntryPointProvider,
):
    """
    The Cotton Candy theme.
    """

    _plugin_id = "cotton-candy"
    _plugin_label = static("Cotton Candy")
    _plugin_description = _("Cotton Candy is Betty's legacy theme.")

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
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
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
    @classmethod
    def new_default_configuration(cls) -> CottonCandyConfiguration:
        return CottonCandyConfiguration()

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self._project)
