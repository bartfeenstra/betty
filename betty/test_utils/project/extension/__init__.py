"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import Generic, TypeVar

from typing_extensions import override

from betty.app import App
from betty.event_dispatcher import EventHandlerRegistry
from betty.project import Project
from betty.project.extension import ConfigurableExtension, Extension
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginTestBase,
    assert_plugin_identifier,
)

_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


class ExtensionTestBase(Generic[_ExtensionT], PluginTestBase[_ExtensionT]):
    """
    A base class for testing :py:class:`betty.project.extension.Extension` implementations.
    """

    async def test_new_for_project(self, new_temporary_app: App) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.new_for_project` implementations.
        """
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await self.get_sut_class().new_for_project(project)
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
            assert_plugin_identifier(
                extension_id,
                Extension,  # type: ignore[type-abstract]
            )

    async def test_comes_after(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_after` implementations.
        """
        for extension_id in self.get_sut_class().comes_after():
            assert_plugin_identifier(
                extension_id,
                Extension,  # type: ignore[type-abstract]
            )

    async def test_comes_before(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_before` implementations.
        """
        for extension_id in self.get_sut_class().comes_before():
            assert_plugin_identifier(
                extension_id,
                Extension,  # type: ignore[type-abstract]
            )

    async def test_register_event_handlers(self, new_temporary_app: App) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.register_event_handlers` implementations.
        """
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await self.get_sut_class().new_for_project(project)
            registry = EventHandlerRegistry()
            sut.register_event_handlers(registry)


class DummyExtension(DummyPlugin, Extension):
    """
    A dummy :py:class:`betty.project.extension.Extension` implementation.
    """


class DummyConfigurableExtension(
    DummyExtension, ConfigurableExtension[DummyConfiguration]
):
    """
    A dummy :py:class:`betty.project.extension.ConfigurableExtension` implementation.
    """

    @override
    @classmethod
    def new_default_configuration(cls) -> DummyConfiguration:
        return DummyConfiguration()
