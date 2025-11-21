from pathlib import Path

import pytest
from typing_extensions import override

from betty.app import App
from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.project.extension import ExtensionDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase
from betty.test_utils.project.extension import DummyExtension


class TestExtensionDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return ExtensionDefinition

    def test_assets_directory_path(self) -> None:
        assets_directory_path = Path(__file__)
        sut = ExtensionDefinition(
            assets_directory_path=assets_directory_path, id="-", label=Plain("")
        )
        assert sut.assets_directory_path == assets_directory_path

    def test_theme(self) -> None:
        sut = ExtensionDefinition(theme=True, id="-", label=Plain(""))
        assert sut.theme


class TestExtensionDocumentation(PluginDocumentationTestBase[ExtensionDefinition]):
    _plugin_type = ExtensionDefinition
    _plugin_type_documentation_path = Path("usage") / "extension.rst"


class TestExtension:
    async def test_project__with___init__(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            sut = DummyExtension(project)
            assert sut.project is project

    async def test_project__with_new(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            assert sut.project is project
