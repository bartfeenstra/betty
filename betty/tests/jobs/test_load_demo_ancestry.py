import pytest

from betty.copyright_notice import CopyrightNotice
from betty.entity.collection.pool import EntityPool
from betty.jobs.load_demo_ancestry import LoadDemoAncestry
from betty.license import License
from betty.service_level import ServiceLevel
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadDemoAncestry:
    async def test_do(self) -> None:
        ancestry = EntityPool()
        await do(
            LoadDemoAncestry(
                ancestry=ancestry,
                factory=ServiceLevel().factory,
                streetmix_copyright_notice=CopyrightNotice(),
                streetmix_license=License(),
            )
        )
        assert len(ancestry)
