"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.service_provider import ServiceProvider, ServiceProviderDefinition

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel


@final
@ServiceProviderDefinition(
    "spdx",
    label=_("SPDX licenses"),
    description=_(
        "Provide license plugins from the SPDX License List ({spdx_url})"
    ).format(spdx_url="https://spdx.org/licenses/"),
)
class Spdx(ServiceProvider, Manufacturable):
    """
    .. plugin:: service-provider:spdx.
    """

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls(services=services)
