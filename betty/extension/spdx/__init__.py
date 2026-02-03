"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.app import App
from betty.extension import Extension, ExtensionDefinition
from betty.license import LicenseDefinition
from betty.license.licenses import SpdxLicenseBuilder
from betty.locale.localizable.gettext import _
from betty.plugin.repository.static import StaticPluginRepository
from betty.service.container import service
from betty.service.level import Manufacturable
from betty.service.requirement.app import require_app
from betty.service.requirement.extension import require_extension

if TYPE_CHECKING:
    from betty.plugin.repository import PluginRepository


@final
@ExtensionDefinition(
    "spdx",
    label=_("SPDX licenses"),
    description=_(
        "Provide license plugins from the SPDX License List (https://spdx.org/licenses/) "
    ),
)
class Spdx(Manufacturable, Extension[App]):
    """
    .. plugin:: extension:spdx.
    """

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
        return cls(services=app)

    @service
    async def license_repository(self) -> PluginRepository[LicenseDefinition]:
        """
        The SPDX licenses.
        """
        return StaticPluginRepository(
            LicenseDefinition,
            *[
                license
                async for license in SpdxLicenseBuilder(  # noqa: A001
                    binary_file_cache=self.services.binary_file_cache.with_scope(
                        "spdx"
                    ),
                    http_client=await self.services.http_client,
                    user=self.services.user,
                ).build()
            ],
        )


LicenseDefinition.type().discoverer.add(
    require_extension(Spdx)(lambda *, extension: extension.license_repository),
)
