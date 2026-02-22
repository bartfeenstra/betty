"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.extension import Extension, ExtensionDefinition
from betty.license import LicenseDefinition
from betty.license.licenses import SpdxLicenseBuilder
from betty.locale.localizable.gettext import _
from betty.plugin.repository.static import StaticPluginRepository
from betty.service.factory import Manufacturable
from betty.service.provider import service
from betty.service.requirement.app import require_app

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

    def __init__(self, *, app: App):
        super().__init__()
        self._app = app

    @override
    @classmethod
    @require_app
    async def new(cls, app: App, /) -> Self:
        return cls(app=app)

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
                    binary_file_cache=self._app.binary_file_cache.with_scope("spdx"),
                    http_client=await self._app.http_client,
                    user=self._app.user,
                ).build()
            ],
        )
