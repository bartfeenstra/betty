"""
Jobs for the Raspberry Mint extension.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final, override

from betty.extensions._theme.search import generate_search_index
from betty.extensions.raspberry_mint import RaspberryMint
from betty.file import write
from betty.job import Job
from betty.locale import to_language_tag
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localizable.plain import Plain
from betty.locale.localize import default_localizer
from betty.os import link_or_copy

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.locale.localizable import Localizable
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
    _result_container_template: Final[Localizable] = Plain("""
    <li class="d-flex gap-2 search-result">
        {{{ betty-search-result }}}
    </li>
    """)

    _results_container_template: Final[Localizable] = Chain(
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
            self._result_container_template,
            self._results_container_template,
            context=scheduler.context,
        )


class _GenerateWebmanifest(Job):
    def __init__(self, *, project: Project):
        super().__init__("raspberry-mint:generate-webmanifest")
        self._project = project

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        raspberry_mint = await self._project.extensions[RaspberryMint]
        webmanifest = json.dumps({
            "name": self._project.title.localize(default_localizer),
            "icons": [
                {"src": "/logo" + self._project.logo.suffix},
            ],
            "lang": to_language_tag(self._project.default_locale.locale),
            "theme_color": raspberry_mint.secondary_color,
            "background_color": "#ffffff",
            "display": "fullscreen",
        })
        await write(self._project.www_directory / "betty.webmanifest", webmanifest)
