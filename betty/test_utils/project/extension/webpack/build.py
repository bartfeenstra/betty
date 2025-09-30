"""
Test utilities for :py:mod:`betty.project.extension.webpack.build`.
"""

from betty.project.extension.webpack.build import EntryPointProvider
from betty.test_utils.project.extension import ExtensionTestBase


class EntryPointProviderTestBase(ExtensionTestBase):
    """
    A base class for testing :py:class:`betty.project.extension.webpack.EntryPointProvider` implementations.
    """

    def test_webpack_entry_point_directory_path(self, sut: EntryPointProvider) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.EntryPointProvider.webpack_entry_point_directory_path` implementations.
        """
        assert type(sut).webpack_entry_point_directory_path().exists()

    async def test_webpack_entry_point_cache_keys(
        self, sut: EntryPointProvider
    ) -> None:
        """
        Tests :py:meth:`betty.project.extension.webpack.EntryPointProvider.webpack_entry_point_cache_keys` implementations.
        """
        sut.webpack_entry_point_cache_keys()
