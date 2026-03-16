"""Provides Betty with SPDX data."""

from __future__ import annotations

from typing import final

from betty.extension import Extension, ExtensionDefinition
from betty.locale.localizable.gettext import _


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
