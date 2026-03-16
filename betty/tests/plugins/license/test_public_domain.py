from typing import override

import pytest

from betty.license import License
from betty.plugins.license.public_domain import PublicDomain
from betty.test_utils.license import LicenseTestBase


class TestPublicDomain(LicenseTestBase):
    @override
    @pytest.fixture
    def sut(self) -> License:
        return PublicDomain()
