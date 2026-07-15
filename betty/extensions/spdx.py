"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import final

from betty.extension import Extension, ExtensionDefinition
from betty.localizables.gettext import _


@final
@ExtensionDefinition(
    "spdx",
    label=_("SPDX licenses"),
    description=_(
        "Provide license plugins from the SPDX License List ({spdx_url})"
    ).format(spdx_url="https://spdx.org/licenses/"),
)
class Spdx(Extension):
    """
    .. plugin:: extension:spdx.
    """
