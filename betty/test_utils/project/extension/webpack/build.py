"""
Test utilities for :py:mod:`betty.project.extension.webpack.build`.
"""

from betty.app import App
from betty.project import Project
from betty.project.extension.webpack.build import EntryPointProvider
from betty.test_utils.project.extension import ExtensionTestBase


class EntryPointProviderTestBase(ExtensionTestBase[EntryPointProvider]):
    """
    A base class for testing :py:class:`betty.project.extension.webpack.EntryPointProvider` implementations.
    """

    def test_webpack_entry_point_directory_path(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.EntryPointProvider.webpack_entry_point_directory_path` implementations.
        """
        assert self.get_sut_class().webpack_entry_point_directory_path().exists()

    async def test_webpack_entry_point_cache_keys(self, new_temporary_app: App) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.EntryPointProvider.webpack_entry_point_cache_keys` implementations.
        """
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await project.new_target(self.get_sut_class())
            sut.webpack_entry_point_cache_keys()
