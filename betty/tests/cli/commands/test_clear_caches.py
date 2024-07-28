from asyncio import to_thread

from betty.app import App
from betty.test_utils.cli import run


class TestClearCaches:
    async def test(self, new_temporary_app: App) -> None:
        await new_temporary_app.cache.set("KeepMeAroundPlease", "")
        await to_thread(run, "clear-caches")
        async with new_temporary_app.cache.get("KeepMeAroundPlease") as cache_item:
            assert cache_item is None
