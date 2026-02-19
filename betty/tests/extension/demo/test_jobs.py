import pytest

from betty.ancestry import Ancestry
from betty.copyright_notice import CopyrightNotice
from betty.extension.demo.jobs import LoadAncestry
from betty.license import License
from betty.service.level import UNIVERSE
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestLoadAncestry:
    async def test_do(self) -> None:
        ancestry = Ancestry()
        await do(
            LoadAncestry(
                ancestry=ancestry,
                factory=UNIVERSE.factory,
                streetmix_copyright_notice=CopyrightNotice(),
                streetmix_license=License(),
            )
        )
        assert len(ancestry)
