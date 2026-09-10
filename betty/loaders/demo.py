"""
Load demonstrative ancestry content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.copyright_notices.streetmix import Streetmix
from betty.factory import Arg1Manufacturable, new
from betty.jobs.load_demo_ancestry import LoadDemoAncestry
from betty.license import LicenseDefinition
from betty.licenses.spdx import spdx_license_id_to_license_id
from betty.load import Loader, LoaderDefinition
from betty.project import Project

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler


@final
@LoaderDefinition("demo", label="Demo")
class Demo(Arg1Manufacturable, Loader):
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
            LoadDemoAncestry(
                project=self._project,
                streetmix_copyright_notice=await new(Streetmix, self._project),
                streetmix_license=await new(
                    (
                        await licenses[
                            spdx_license_id_to_license_id("AGPL-3.0-or-later")
                        ]
                    ).cls,
                    self._project,
                ),
            )
        )
