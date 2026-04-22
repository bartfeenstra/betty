"""
Load demonstrative ancestry content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.factory import Manufacturable
from betty.license import LicenseDefinition
from betty.load import Loader, LoaderDefinition
from betty.plugins.copyright_notice.streetmix import Streetmix
from betty.plugins.license.spdx import spdx_license_id_to_license_id
from betty.plugins.loader.demo.jobs import LoadAncestry
from betty.project import Project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@LoaderDefinition("demo", label="Demo")
class Demo(Manufacturable, Loader):
    """
    .. plugin:: loader:demo.
    """

    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @override
    async def load(self, scheduler: Scheduler, /) -> None:
        licenses = self._project.plugins[LicenseDefinition]
        await scheduler.add(
            LoadAncestry(
                ancestry=self._project.ancestry,
                factory=self._project.factory,
                streetmix_copyright_notice=await self._project.factory.new(Streetmix),
                streetmix_license=await self._project.factory.new(
                    (
                        await licenses[
                            spdx_license_id_to_license_id("AGPL-3.0-or-later")
                        ]
                    ).cls
                ),
            )
        )
