from pathlib import Path

import pytest
from typing_extensions import override

from betty.app import App
from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.project.extension import ExtensionDefinition
from betty.requirement import Requirement
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin.classed import ClassedPluginDefinitionClassTestBase
from betty.test_utils.project.extension import DummyExtensionOne


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
        with ExtensionDefinition.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_temporary(temporary_app) as project:
                project.configuration.extensions.enable(DummyExtensionOne)
                async with project:
                    requires = await DummyExtensionOne.requires(project, "")
        assert isinstance(requires, DummyExtensionOne)
