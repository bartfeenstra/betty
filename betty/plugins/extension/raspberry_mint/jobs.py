"""
Jobs for the Raspberry Mint extension.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, override

import aiofiles

from betty.job import Job
from betty.locale import to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.os import link_or_copy
from betty.plugins.extension._theme.search import generate_search_index
from betty.plugins.extension.raspberry_mint import RaspberryMint

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


class _GenerateLogo(Job):
    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-logo")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await link_or_copy(
            self._project.logo,
            self._project.www_directory / ("logo" + self._project.logo.suffix),
        )


class _GenerateSearchIndex(Job):
    _RESULT_CONTAINER_TEMPLATE = Plain("""
    <li class="d-flex gap-2 search-result">
        {{{ betty-search-result }}}
    </li>
    """)

    _RESULTS_CONTAINER_TEMPLATE = Chain(
        '<ul class="entity-list"><h3 class="h2">',
        _("Results ({{{ betty-search-results-count }}})"),
        "</h3>{{{ betty-search-results }}}</ul>",
    )

    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-search-index")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await generate_search_index(
            self._project,
            self._RESULT_CONTAINER_TEMPLATE,
            self._RESULTS_CONTAINER_TEMPLATE,
            context=scheduler.context,
        )


class _GenerateWebmanifest(Job):
    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-webmanifest")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        extensions = await self._project.extensions
        webmanifest = json.dumps(
            {
                "name": self._project.configuration.title.localize(DEFAULT_LOCALIZER),
                "icons": [
                    {"src": "/logo" + self._project.logo.suffix},
                ],
                "lang": to_language_tag(
                    self._project.configuration.default_locale.locale
                ),
                "theme_color": extensions[RaspberryMint].secondary_color,
                "background_color": "#ffffff",
                "display": "fullscreen",
            }
        )
        async with aiofiles.open(
            self._project.www_directory / "betty.webmanifest", "w"
        ) as f:
            await f.write(webmanifest)
