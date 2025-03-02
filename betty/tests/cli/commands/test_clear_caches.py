from betty.app import App
from betty.test_utils.cli import run


class TestClearCaches:
    async def test_click_command(self, new_temporary_app_cli: App) -> None:
        await new_temporary_app_cli.cache.set("KeepMeAroundPlease", "")
        await run(new_temporary_app_cli, "clear-caches")
        async with new_temporary_app_cli.cache.get("KeepMeAroundPlease") as cache_item:
            assert cache_item is None
