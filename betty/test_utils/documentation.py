"""
Documentation testing utilities.
"""

from typing import Any

import pytest

from betty.importlib import fully_qualified_name
from betty.plugin.cls import PluginClsDefinition
from betty.test_utils.conftest import (
    IsolatedAppFactory,
    IsolatedProjectFactory,
)
from betty.universe import UNIVERSE


class PluginDocumentationTestBase:
    """
    Test a module's plugin and plugin type documentation.
    """

    _module: str

    def _match_module(self, target: Any) -> bool:
        module = getattr(target, "__module__", "")
        assert isinstance(module, str)
        return module.startswith(self._module)

    async def test(
        self,
        isolated_app_factory: IsolatedAppFactory,
        isolated_project_factory: IsolatedProjectFactory,
        subtests: pytest.Subtests,
    ) -> None:
        """
        Test the plugin and plugin type documentation.
        """
        async with (
            isolated_app_factory() as app,
            isolated_project_factory(app=app) as project,
        ):
            for plugin_type in UNIVERSE.plugins:
                with subtests.test():
                    self._test_plugin_type(plugin_type.type)
                async for plugin in project.plugins[plugin_type.type]:
                    with subtests.test():
                        self._test_plugin(plugin)

    def _test_plugin_type(self, plugin_type: type[PluginClsDefinition]) -> None:
        if not self._match_module(plugin_type):
            return
        if plugin_type.type().id.startswith("-"):
            return
        docstring = plugin_type.__doc__ or ""
        directive = f".. plugin_type:: {plugin_type.type().id}"
        assert directive in docstring, (
            f'Failed to find the "{directive}" directive in the docstring for {fully_qualified_name(plugin_type)}'
        )

    def _test_plugin(self, plugin: PluginClsDefinition) -> None:
        if not self._match_module(plugin.cls):
            return
        if plugin.id.startswith("-"):
            return
        docstring = plugin.cls.__doc__ or ""
        directive = f".. plugin:: {plugin.type().id}:{plugin.id}"
        assert directive in docstring, (
            f'Failed to find the "{directive}" directive in the docstring for {fully_qualified_name(plugin.cls)}'
        )
