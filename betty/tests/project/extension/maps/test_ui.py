from collections.abc import Iterable

import pytest
from typing_extensions import override

from betty.project.extension import Extension
from betty.test_utils.project.extension.maps import MapsTestBase


@pytest.mark.xfail(
    reason="This has been failing for Webkit on Github Actions since June 25, 2025. Cause unknown."
)
class TestMaps(MapsTestBase):
    @override
    def get_other_extensions(self) -> Iterable[type[Extension]]:
        return ()
