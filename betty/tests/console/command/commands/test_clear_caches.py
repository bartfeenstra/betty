from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.clear_caches import ClearCaches
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandTestBase


class TestClearCaches(CommandTestBase):
    @override
    def get_sut_class(self) -> type[Command]:
        return ClearCaches

    async def test_configure(self, new_temporary_app: App) -> None:
        await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        await run(new_temporary_app, "clear-caches")
        async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
            assert cache_item is None
