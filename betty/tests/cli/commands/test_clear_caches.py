from betty.app import App
from betty.test_utils.cli import run


class TestClearCaches:
    async def test_click_command(self, new_temporary_app: App) -> None:
        await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        await run(new_temporary_app, "clear-caches")
        async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
            assert cache_item is None
