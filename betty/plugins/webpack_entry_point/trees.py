"""Provide interactive family trees by integrating Betty with `Cytoscape.js <https://cytoscape.org/>`_."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.dirs import ROOT_DIRECTORY_PATH
from betty.webpack import WebpackEntryPoint, WebpackEntryPointDefinition

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
@WebpackEntryPointDefinition(
    "trees", entry_point=ROOT_DIRECTORY_PATH / "webpack-entry-points" / "trees"
)
class Trees(WebpackEntryPoint):
    """
    .. plugin:: webpack-entry-point:trees.
    """

    # Provide an initializer without arguments so the factory can call it.
    def __init__(self):
        super().__init__()

    @override
    async def cache_keys(self) -> Sequence[str]:
        return ()
