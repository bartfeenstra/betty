from typing import override

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.copyright_notices.project_author import ProjectAuthor
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestProjectAuthor(CopyrightNoticeTestBase):
    @override
    @pytest.fixture(
        params=[
            None,
            "My First Author",
        ]
    )
    def sut(self, request: pytest.FixtureRequest) -> CopyrightNotice:
        return ProjectAuthor(request.param)
