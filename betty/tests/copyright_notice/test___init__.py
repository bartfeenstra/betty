import pytest
from typing_extensions import override

from betty.copyright_notice import CopyrightNoticeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestCopyrightNoticeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CopyrightNoticeDefinition
