"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, final, Self

import aiofiles
from typing_extensions import override

from betty.html import CssProvider
from betty.jinja2 import (
    Jinja2Provider,
    Filters,
)
from betty.locale.localizable import static, call, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.os import link_or_copy
from betty.plugin import ShorthandPluginBase
from betty.project.extension import Theme, Extension, ConfigurableExtension
from betty.project.extension._theme import jinja2_filters
from betty.project.extension._theme.search import generate_search_index
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
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


async def _generate_logo(event: GenerateSiteEvent) -> None:
    await link_or_copy(
        event.project.logo,
        event.project.configuration.www_directory_path
        / ("logo" + event.project.logo.suffix),
    )


_RESULT_CONTAINER_TEMPLATE = plain("""
<li class="d-flex gap-2 search-result">
    {{{ betty-search-result }}}
</li>
""")

_RESULTS_CONTAINER_TEMPLATE = call(
    lambda localizer: '<ul class="entity-list"><h3 class="h2">'
    + localizer._("Results ({{{ betty-search-results-count }}})")
    + "</h3>{{{ betty-search-results }}}</ul>"
)


async def _generate_search_index(event: GenerateSiteEvent) -> None:
    await generate_search_index(
        event.project,
        _RESULT_CONTAINER_TEMPLATE,
        _RESULTS_CONTAINER_TEMPLATE,
        job_context=event.job_context,
    )


async def _generate_webmanifest(event: GenerateSiteEvent) -> None:
    project = event.project
    extensions = await project.extensions
    webmanifest = json.dumps(
        {
            "name": project.configuration.title.localize(DEFAULT_LOCALIZER),
            "icons": [
                {"src": "/logo" + project.logo.suffix},
            ],
            "lang": project.configuration.locales.default.locale,
            "theme_color": extensions[RaspberryMint].configuration.secondary_color.hex,
            "background_color": "#ffffff",
            "display": "fullscreen",
        }
    )
    async with aiofiles.open(
        project.configuration.www_directory_path / "betty.webmanifest", "w"
    ) as f:
        await f.write(webmanifest)


@final
class RaspberryMint(
    ShorthandPluginBase,
    Theme,
    CssProvider,
    ConfigurableExtension[RaspberryMintConfiguration],
    Jinja2Provider,
    EntryPointProvider,
):
    """
    The Raspberry Mint theme.
    """

    _plugin_id = "raspberry-mint"
    _plugin_label = static("Raspberry Mint")

    @private
    def __init__(
        self,
        project: Project,
        public_css_paths: Sequence[str],
        *,
        configuration: RaspberryMintConfiguration,
    ):
        super().__init__(project, configuration=configuration)
        self._public_css_paths = public_css_paths

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        url_generator = await project.url_generator
        return cls(
            project,
            [url_generator.generate("betty-static:///css/raspberry-mint.css")],
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
        registry.add_handler(
            GenerateSiteEvent,
            _generate_logo,
            _generate_search_index,
            _generate_webmanifest,
        )

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
            self._configuration.primary_color.hex,
            self._configuration.secondary_color.hex,
            self._configuration.tertiary_color.hex,
        )

    @override
    @property
    def public_css_paths(self) -> Sequence[str]:
        return self._public_css_paths

    @override
    @classmethod
    def new_default_configuration(cls) -> RaspberryMintConfiguration:
        return RaspberryMintConfiguration()

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self._project)
