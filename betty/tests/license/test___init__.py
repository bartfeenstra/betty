from pathlib import Path

import pytest
from typing_extensions import override

from betty.license import LicenseDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestLicenseDefinition(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return LicenseDefinition


class TestLicenseDocumentation(PluginDocumentationTestBase[LicenseDefinition]):
    _plugin_type = LicenseDefinition
    _plugin_type_documentation_path = Path("usage") / "license.rst"
