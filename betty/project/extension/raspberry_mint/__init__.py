"""
Provide the Raspberry Mint theme.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, final

import aiofiles
from typing_extensions import override

from betty.jinja2 import (
    Filters,
    Jinja2Provider,
)
from betty.job import Job
from betty.locale.localizable import Join, Plain, StaticTranslations, _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.os import link_or_copy
from betty.plugin import ShorthandPluginBase
from betty.project import ProjectContext
from betty.project.extension import ConfigurableExtension, Extension, Theme
from betty.project.extension._theme import jinja2_filters
from betty.project.extension._theme.search import generate_search_index
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.webpack.build import EntryPointProvider
from betty.project.generate import Generator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.job.scheduler import Scheduler
    from betty.plugin import PluginIdentifier


class _GenerateLogo(Job[ProjectContext]):
    def __init__(self):
        super().__init__("raspberry-mint:generate-logo")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        await link_or_copy(
            project.logo,
            project.configuration.www_directory_path / ("logo" + project.logo.suffix),
        )


class _GenerateSearchIndex(Job[ProjectContext]):
    _RESULT_CONTAINER_TEMPLATE = Plain("""
    <li class="d-flex gap-2 search-result">
        {{{ betty-search-result }}}
    </li>
    """)

    _RESULTS_CONTAINER_TEMPLATE = Join(
        "",
        '<ul class="entity-list"><h3 class="h2">',
        _("Results ({{{ betty-search-results-count }}})"),
        "</h3>{{{ betty-search-results }}}</ul>",
    )

    def __init__(self):
        super().__init__("raspberry-mint:generate-search-index")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        context = scheduler.context
        await generate_search_index(
            context.project,
            self._RESULT_CONTAINER_TEMPLATE,
            self._RESULTS_CONTAINER_TEMPLATE,
            job_context=context,
        )


class _GenerateWebmanifest(Job[ProjectContext]):
    def __init__(self):
        super().__init__("raspberry-mint:generate-webmanifest")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        extensions = await project.extensions
        webmanifest = json.dumps(
            {
                "name": project.configuration.title.localize(DEFAULT_LOCALIZER),
                "icons": [
                    {"src": "/logo" + project.logo.suffix},
                ],
                "lang": project.configuration.locales.default.locale,
                "theme_color": extensions[
                    RaspberryMint
                ].configuration.secondary_color.hex,
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
    ConfigurableExtension[RaspberryMintConfiguration],
    Jinja2Provider,
    Generator,
    EntryPointProvider,
):
    """
    The Raspberry Mint theme.
    """

    _plugin_id = "raspberry-mint"
    _plugin_label = StaticTranslations("Raspberry Mint")

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
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(
            _GenerateLogo(),
            _GenerateSearchIndex(),
            _GenerateWebmanifest(),
        )

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
            self._configuration.primary_color.hex,
            self._configuration.secondary_color.hex,
            self._configuration.tertiary_color.hex,
        )

    @override
    @classmethod
    def new_default_configuration(cls) -> RaspberryMintConfiguration:
        return RaspberryMintConfiguration()

    @override
    @property
    def filters(self) -> Filters:
        return jinja2_filters(self._project)
