from pathlib import Path

import pytest
from typing_extensions import override

from betty.app import App
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.project.extension import ExtensionPlugin
from betty.requirement import Requirement
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.plugin import PluginDefinitionClassTestBase
from betty.test_utils.project.extension import DummyExtensionOne


class TestExtensionPlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return ExtensionPlugin

    def test_assets_directory_path(self) -> None:
        assets_directory_path = Path(__file__)
        sut = ExtensionPlugin(
            "-", assets_directory_path=assets_directory_path, label=DUMMY_LOCALIZABLE
        )
        assert sut.assets_directory_path == assets_directory_path

    def test_theme(self) -> None:
        sut = ExtensionPlugin("-", theme=True, label=DUMMY_LOCALIZABLE)
        assert sut.theme


class TestExtensionDocumentation(PluginDocumentationTestBase[ExtensionPlugin]):
    _plugin_type = ExtensionPlugin
    _plugin_type_documentation_path = Path("usage") / "extension.rst"


class TestExtension:
    async def test_requires__with_global(self) -> None:
        subject = "My First Subject"
        requires = await DummyExtensionOne.requires(None, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires__with_app(self, temporary_app: App) -> None:
        subject = "My First Subject"
        requires = await DummyExtensionOne.requires(temporary_app, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires__with_project_without_extension(
        self, temporary_app: App
    ) -> None:
        subject = "My First Subject"
        async with Project.new_temporary(temporary_app) as project, project:
            requires = await DummyExtensionOne.requires(project, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires__with_project_with_extension(
        self, temporary_app: App
    ) -> None:
        with ExtensionPlugin.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(DummyExtensionOne)
                async with project:
                    requires = await DummyExtensionOne.requires(project, "")
        assert isinstance(requires, DummyExtensionOne)
