from __future__ import annotations

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.entity.collection.pool import EntityPool
from betty.license import License
from betty.loaders.demo import LoadAncestry
from betty.service_level import ServiceLevel
from betty.test_utils.job import do


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_load_ancestry() -> None:
    ancestry = EntityPool()
    await do(
        LoadAncestry(
            ancestry=ancestry,
            factory=ServiceLevel().factory,
            streetmix_copyright_notice=CopyrightNotice(),
            streetmix_license=License(),
        )
    )
    assert len(ancestry)
