from betty.asset_directories import builtin
from betty.services.asset import HasAssets


class TestHasAssets:
    async def test_assets(self) -> None:
        async with HasAssets() as sut:
            assert list(sut.assets.directories) == [builtin.assets]
