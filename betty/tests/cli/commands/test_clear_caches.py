from betty.app import App
from betty.test_utils.cli import run


class TestClearCaches:
    async def test(self) -> None:
        async with App.new_temporary() as app, app:
            await app.cache.set("KeepMeAroundPlease", "")
            await run(app, "clear-caches")
            async with app.cache.get("KeepMeAroundPlease") as cache_item:
                assert cache_item is None
