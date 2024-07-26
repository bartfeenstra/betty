from __future__ import annotations

from typing import TYPE_CHECKING

from betty.fs import ASSETS_DIRECTORY_PATH
from betty.test_utils.locale import PotFileTestBase
from typing_extensions import override

if TYPE_CHECKING:
    from pathlib import Path


class TestPotFile(PotFileTestBase):
    @override
    def assets_directory_path(self) -> Path:
        return ASSETS_DIRECTORY_PATH

    @override
    def command(self) -> str:
        return "betty dev-update-translations"
