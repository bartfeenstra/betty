from typing import override

import pytest

from betty.license import License
from betty.licenses.all_rights_reserved import AllRightsReserved
from betty.test_utils.license import LicenseTestBase


class TestAllRightsReserved(LicenseTestBase):
    @override
    @pytest.fixture
    def sut(self) -> License:
        return AllRightsReserved()
