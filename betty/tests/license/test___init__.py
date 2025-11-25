from pathlib import Path

import pytest
from typing_extensions import override

from betty.license import LicensePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestLicensePlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return LicensePlugin


class TestLicenseDocumentation(PluginDocumentationTestBase[LicensePlugin]):
    _plugin_type = LicensePlugin
    _plugin_type_documentation_path = Path("usage") / "license.rst"
