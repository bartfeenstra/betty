from pathlib import Path

import pytest
from typing_extensions import override

from betty.copyright_notice import CopyrightNoticePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase


class TestCopyrightNoticePlugin(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CopyrightNoticePlugin


class TestCopyrightNoticeDocumentation(
    PluginDocumentationTestBase[CopyrightNoticePlugin]
):
    _plugin_type = CopyrightNoticePlugin
    _plugin_type_documentation_path = Path("usage") / "copyright-notice.rst"
