from collections.abc import Sequence
from graphlib import TopologicalSorter

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.event_dispatcher import EventHandlerRegistry
from betty.plugin import PluginIdentifier
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.extension import sort_extension_type_graph, Extension
from betty.test_utils.project.extension import DummyExtension


class TestExtension:
    async def test_project_with___init__(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = DummyExtension(project)
            assert sut.project is project

    async def test_project_with_new(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            assert sut.project is project

    async def test_register_event_handlers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            sut = await DummyExtension.new_for_project(project)
            sut.register_event_handlers(EventHandlerRegistry())


class ComesBeforeTargetExtension(DummyExtension):
    pass


class DependsOnComesBeforeTargetExtension(DummyExtension):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesBeforeTargetExtension}


class HasComesBeforeExtension(DummyExtension):
    @override
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesBeforeTargetExtension}


class ComesAfterTargetExtension(DummyExtension):
    pass


class DependsOnHasComesAfterTargetExtension(DummyExtension):
    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesAfterTargetExtension}


class HasComesAfterExtension(DummyExtension):
    @override
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {ComesAfterTargetExtension}


class TestSortExtensionTypeGraph:
    @pytest.mark.parametrize(
        ("expected", "initial"),
        [
            (
                [],
                [],
            ),
            (
                [HasComesBeforeExtension],
                [HasComesBeforeExtension],
            ),
            (
                [HasComesAfterExtension],
                [HasComesAfterExtension],
            ),
            (
                [ComesBeforeTargetExtension, DependsOnComesBeforeTargetExtension],
                [DependsOnComesBeforeTargetExtension],
            ),
            (
                [ComesAfterTargetExtension, DependsOnHasComesAfterTargetExtension],
                [DependsOnHasComesAfterTargetExtension],
            ),
            (
                [ComesBeforeTargetExtension, DependsOnComesBeforeTargetExtension],
                [DependsOnComesBeforeTargetExtension, ComesBeforeTargetExtension],
            ),
            (
                [ComesAfterTargetExtension, DependsOnHasComesAfterTargetExtension],
                [DependsOnHasComesAfterTargetExtension, ComesAfterTargetExtension],
            ),
            (
                [
                    HasComesBeforeExtension,
                    ComesBeforeTargetExtension,
                    DependsOnComesBeforeTargetExtension,
                ],
                [DependsOnComesBeforeTargetExtension, HasComesBeforeExtension],
            ),
            (
                [
                    ComesAfterTargetExtension,
                    DependsOnHasComesAfterTargetExtension,
                    HasComesAfterExtension,
                ],
                [DependsOnHasComesAfterTargetExtension, HasComesAfterExtension],
            ),
        ],
    )
    async def test(
        self,
        expected: list[type[DummyExtension]],
        initial: Sequence[type[DummyExtension]],
        mocker: MockerFixture,
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository[Extension](
                ComesBeforeTargetExtension,
                DependsOnComesBeforeTargetExtension,
                HasComesBeforeExtension,
                ComesAfterTargetExtension,
                DependsOnHasComesAfterTargetExtension,
                HasComesAfterExtension,
            ),
        )
        sorter = TopologicalSorter[type[Extension]]()
        await sort_extension_type_graph(sorter, initial)
        assert list(sorter.static_order()) == expected
