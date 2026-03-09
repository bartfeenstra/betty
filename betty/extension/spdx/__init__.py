"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.extension import Extension, ExtensionDefinition
from betty.license.licenses import SpdxLicenseBuilder
from betty.locale.localizable.gettext import _
from betty.service.requirement.extension import require_extension
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.license import LicenseDefinition
    from betty.project import Project


@final
@ExtensionDefinition(
    "spdx",
    label=_("SPDX licenses"),
    description=_(
        "Provide license plugins from the SPDX License List (https://spdx.org/licenses/) "
    ),
)
class Spdx(Extension):
    """
    .. plugin:: extension:spdx.
    """

    # Provide an initializer without arguments so the factory can call it.
    def __init__(self):
        super().__init__()


@require_project
async def discover_licenses(project: Project) -> Iterable[LicenseDefinition]:
    """
    Discover the SPDX licenses.
    """
    await require_extension(Spdx)(project)
    return [
        license
        async for license in SpdxLicenseBuilder(  # noqa: A001
            binary_file_cache=project.app.binary_file_cache.with_scope("spdx"),
            http_client=await project.app.http_client,
            user=project.app.user,
        ).build()
    ]
