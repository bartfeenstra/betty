from __future__ import annotations

from typing_extensions import override

from betty.project.extension.privatizer import Privatizer
from betty.test_utils.project.extension import ExtensionTestBase


class TestPrivatizer(ExtensionTestBase[Privatizer]):
    @override
    def get_sut_class(self) -> type[Privatizer]:
        return Privatizer
