"""
Test utilities for :py:module:`betty.project.extension`.
"""

from betty.app import App
from betty.machine_name import assert_machine_name
from betty.project import Project
from betty.project.extension import Extension
from betty.test_utils.plugin import DummyPlugin, PluginTestBase


class ExtensionTestBase(PluginTestBase[Extension]):
    """
    A base class for testing :py:class:`betty.project.extension.Extension` implementations.
    """

    async def test_new_for_project(self, new_temporary_app: App) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.new_for_project` implementations.
        """
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = self.get_sut_class().new_for_project(project)
            assert sut.project == project

    async def test_assets_directory_path(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.assets_directory_path` implementations.
        """
        assets_directory_path = self.get_sut_class().assets_directory_path()
        if assets_directory_path is not None:
            assert assets_directory_path.is_dir()

    async def test_depends_on(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.depends_on` implementations.
        """
        for extension_id in self.get_sut_class().depends_on():
            assert_machine_name()(extension_id)

    async def test_comes_after(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_after` implementations.
        """
        for extension_id in self.get_sut_class().comes_after():
            assert_machine_name()(extension_id)

    async def test_comes_before(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_before` implementations.
        """
        for extension_id in self.get_sut_class().comes_before():
            assert_machine_name()(extension_id)


class DummyExtension(DummyPlugin, Extension):
    """
    A dummy extension implementation.
    """

    pass
