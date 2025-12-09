from pathlib import Path

import pytest
from typing_extensions import override

from betty.copyright_notice import CopyrightNoticeDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestCopyrightNoticeDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return CopyrightNoticeDefinition


class TestCopyrightNoticeDocumentation(
    PluginDocumentationTestBase[CopyrightNoticeDefinition]
):
    _plugin_type = CopyrightNoticeDefinition
    _plugin_type_documentation_path = Path("usage") / "copyright-notice.rst"
