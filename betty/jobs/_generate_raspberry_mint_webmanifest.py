from __future__ import annotations

import json
from typing import TYPE_CHECKING, final, override

from betty.extensions.raspberry_mint import RaspberryMint
from betty.file import write
from betty.job import Job
from betty.locale import to_language_tag
from betty.localizer import default_localizer

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class _GenerateRaspberryMintWebmanifest(Job):
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
