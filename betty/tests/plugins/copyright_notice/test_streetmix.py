from typing import override

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.plugins.copyright_notice.streetmix import Streetmix
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestStreetmix(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return Streetmix()
