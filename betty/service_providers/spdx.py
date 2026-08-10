"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import final

from betty.localizables.gettext import _
from betty.service_provider import ServiceProvider, ServiceProviderDefinition


@final
@ServiceProviderDefinition(
    "spdx",
    label=_("SPDX licenses"),
    description=_(
        "Provide license plugins from the SPDX License List ({spdx_url})"
    ).format(spdx_url="https://spdx.org/licenses/"),
)
class Spdx(ServiceProvider):
    """
    .. plugin:: service-provider:spdx.
    """
