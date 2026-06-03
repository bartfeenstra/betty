from typing import override

import pytest

from betty.copyright_notice import CopyrightNotice
from betty.copyright_notices.public_domain import PublicDomain
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestPublicDomain(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return PublicDomain()
