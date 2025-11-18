"""
Documentation testing utilities.
"""

from collections.abc import Collection
from pathlib import Path
from typing import Generic, TypeVar

import aiofiles

from betty.app import App
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.plugin import PluginDefinition
from betty.project import Project

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


class PluginDocumentationTestBase(Generic[_PluginDefinitionT]):
    """
    Test a plugin type's documentation.
    """

    _plugin_type: type[_PluginDefinitionT]
    _plugin_type_documentation_path: Path

    async def test_should_contain_plugins(self, temporary_app: App) -> None:
        """
        Test that the plugin type's documentation includes all its plugins.
        """
        documentation_file_path = (
            ROOT_DIRECTORY_PATH / "documentation" / self._plugin_type_documentation_path
        )
        async with aiofiles.open(documentation_file_path) as f:
            documentation = await f.read()
        async with Project.new_temporary(temporary_app) as project, project:
            for plugin in await project.plugins(self._plugin_type):
                if plugin.id.startswith("-"):
                    continue
                for expected in self._get_expected(plugin):
                    assert expected in documentation, (
                        f'Failed to find "{expected}" in the documentation at {documentation_file_path}'
                    )

    def _get_expected(self, plugin: _PluginDefinitionT) -> Collection[str]:
        return (plugin.type.id,)
