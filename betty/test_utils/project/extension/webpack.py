"""
Test utilities for :py:mod:`betty.project.extension.webpack`.
"""

from betty.app import App
from betty.project import Project
from betty.project.extension.webpack import WebpackEntryPointProvider
from betty.test_utils.project.extension import ExtensionTestBase


class WebpackEntryPointProviderTestBase(ExtensionTestBase[WebpackEntryPointProvider]):
    """
    A base class for testing :py:class:`betty.project.extension.webpack.WebpackEntryPointProvider` implementations.
    """

    def test_webpack_entry_point_directory_path(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.WebpackEntryPointProvider.webpack_entry_point_directory_path` implementations.
        """
        assert self.get_sut_class().webpack_entry_point_directory_path().exists()

    async def test_webpack_entry_point_cache_keys(self, new_temporary_app: App) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.WebpackEntryPointProvider.webpack_entry_point_cache_keys` implementations.
        """
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            sut.webpack_entry_point_cache_keys()
