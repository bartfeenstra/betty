"""
Jobs for the Raspberry Mint extension.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import aiofiles
from typing_extensions import override

from betty.job import Job
from betty.locale import to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.os import link_or_copy
from betty.project import ProjectContext
from betty.project.extension._theme.search import generate_search_index
from betty.project.extension.raspberry_mint import RaspberryMint

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


class _GenerateLogo(Job[ProjectContext]):
    def __init__(self):
        super().__init__("raspberry-mint:generate-logo")

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        project = scheduler.context.project
        await link_or_copy(
            project.logo,
            project.www_directory_path / ("logo" + project.logo.suffix),
        )


class _GenerateSearchIndex(Job[ProjectContext]):
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
                "lang": to_language_tag(project.configuration.locales.default.locale),
                "theme_color": extensions[
                    RaspberryMint
                ].configuration.secondary_color.hex,
                "background_color": "#ffffff",
                "display": "fullscreen",
            }
        )
        async with aiofiles.open(
            project.www_directory_path / "betty.webmanifest", "w"
        ) as f:
            await f.write(webmanifest)
