"""
Render interactive maps.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.dirs import ROOT_DIRECTORY
from betty.webpack import WebpackEntryPoint, WebpackEntryPointDefinition

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
@WebpackEntryPointDefinition(
    "map", entry_point=ROOT_DIRECTORY / "webpack-entry-points" / "maps"
)
class Maps(WebpackEntryPoint):
    """
    .. plugin:: webpack-entry-point:maps.
    """

    # Provide an initializer without arguments so the factory can call it.
    def __init__(self):
        super().__init__()

    @override
    async def cache_keys(self) -> Sequence[str]:
        return ()
