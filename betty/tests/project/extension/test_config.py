from betty.project.extension.config import ExtensionInstanceConfiguration
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.project.extension import (
    DummyExtension,
    DummyConfigurableExtension,
)


class TestExtensionInstanceConfiguration:
    def test_without_configuration(self) -> None:
        plugin = DummyExtension
        sut = ExtensionInstanceConfiguration(plugin)
        assert sut.plugin is plugin

    def test_with_configuration(self) -> None:
        plugin = DummyConfigurableExtension
        configuration = DummyConfiguration()
        sut = ExtensionInstanceConfiguration(plugin, configuration=configuration)
        assert sut.plugin is plugin
        assert sut.configuration is configuration
