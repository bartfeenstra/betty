"""
Test utilities for :py:mod:`betty.project.extension`.
"""

from typing import Self

from typing_extensions import override

from betty.app import App
from betty.assertion import assert_record, RequiredField, assert_bool, assert_setattr
from betty.config import Configuration
from betty.event_dispatcher import EventHandlerRegistry
from betty.project import Project
from betty.project.extension import Extension, ConfigurableExtension
from betty.serde.dump import Dump
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginTestBase,
    assert_plugin_identifier,
)
from betty.typing import Voidable


class ExtensionTestBase(PluginTestBase[Extension]):
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
            await assert_plugin_identifier(
                extension_id,
                Extension,  # type: ignore[type-abstract]
            )

    async def test_comes_after(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_after` implementations.
        """
        for extension_id in self.get_sut_class().comes_after():
            await assert_plugin_identifier(
                extension_id,
                Extension,  # type: ignore[type-abstract]
            )

    async def test_comes_before(self) -> None:
        """
        Tests :py:meth:`betty.project.extension.Extension.comes_before` implementations.
        """
        for extension_id in self.get_sut_class().comes_before():
            await assert_plugin_identifier(
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

    pass


class DummyConfigurableExtensionConfiguration(Configuration):
    """
    A dummy :py:class:`betty.config.Configuration` implementation for :py:class:`betty.test_utils.project.extension.DummyConfigurableExtension`.
    """

    def __init__(self, *, check: bool = False):
        super().__init__()
        self.check = check

    @override
    def update(self, other: Self) -> None:
        self.check = other.check

    @override
    async def load(self, dump: Dump) -> None:
        await assert_record(
            RequiredField("check", assert_bool() | assert_setattr(self, "check"))
        )(dump)

    @override
    def dump(self) -> Voidable[Dump]:
        return {
            "check": self.check,
        }


class DummyConfigurableExtension(
    DummyExtension, ConfigurableExtension[DummyConfigurableExtensionConfiguration]
):
    """
    A dummy :py:class:`betty.project.extension.ConfigurableExtension` implementation.
    """

    @override
    @classmethod
    def default_configuration(cls) -> DummyConfigurableExtensionConfiguration:
        return DummyConfigurableExtensionConfiguration()
