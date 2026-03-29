import pytest

from betty.copyright_notice import CopyrightNotice
from betty.entity.collection.pool import EntityPool
from betty.license import License
from betty.plugins.extension.demo import LoadAncestry
from betty.service.level.universe import UNIVERSE
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadAncestry:
    async def test_do(self) -> None:
        ancestry = EntityPool()
        await do(
            LoadAncestry(
                ancestry=ancestry,
                factory=UNIVERSE.factory,
                streetmix_copyright_notice=CopyrightNotice(),
                streetmix_license=License(),
            )
        )
        assert len(ancestry)
