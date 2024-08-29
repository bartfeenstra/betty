from __future__ import annotations

from typing import TYPE_CHECKING

from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.translation import update_dev_translations
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
        return "betty dev-update-translations"  # pragma: no cover

    @override
    async def update_translations(
        self, output_assets_directory_path_override: Path
    ) -> None:
        await update_dev_translations(
            _output_assets_directory_path_override=output_assets_directory_path_override
        )
