from collections.abc import AsyncIterator, Sequence

import pytest
from typing_extensions import override

from betty.machine_name import MachineName
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
)
from betty.test_utils.plugin import DummyPlugin


class TestPluginNotFound:
    async def test_new(self) -> None:
        PluginNotFound.new("my-first-plugin-id")


class TestPlugin:
    async def test_plugin_description(self) -> None:
        Plugin.plugin_description()


class _TestPluginRepositoryMixinOne:
    pass


class _TestPluginRepositoryMixinTwo:
    pass


class _TestPluginRepositoryMixinThree:
    pass


class _TestPluginRepositoryPluginOne(DummyPlugin, _TestPluginRepositoryMixinOne):
    pass


class _TestPluginRepositoryPluginOneTwo(
    DummyPlugin,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
):
    pass


class _TestPluginRepositoryPluginOneTwoThree(
    DummyPlugin,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
    _TestPluginRepositoryMixinThree,
):
    pass


class _TestPluginRepositoryPluginRepository(PluginRepository[DummyPlugin]):
    def __init__(self, *plugins: type[DummyPlugin]):
        self._plugins = {plugin.plugin_id(): plugin for plugin in plugins}

    @override
    async def get(self, plugin_id: MachineName) -> type[DummyPlugin]:
        return self._plugins[plugin_id]

    @override
    async def __aiter__(self) -> AsyncIterator[type[DummyPlugin]]:
        for plugin in self._plugins.values():
            yield plugin


class TestPluginRepository:
    async def test_select_without_plugins(self) -> None:
        sut = _TestPluginRepositoryPluginRepository()
        assert len(await sut.select()) == 0

    @pytest.mark.parametrize(
        (
            "expected",
            "mixins",
        ),
        [
            (
                (
                    _TestPluginRepositoryPluginOne,
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {},
            ),
            (
                (
                    _TestPluginRepositoryPluginOne,
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinOne},
            ),
            (
                (
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinOne, _TestPluginRepositoryMixinTwo},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {
                    _TestPluginRepositoryMixinOne,
                    _TestPluginRepositoryMixinTwo,
                    _TestPluginRepositoryMixinThree,
                },
            ),
            (
                (
                    _TestPluginRepositoryPluginOneTwo,
                    _TestPluginRepositoryPluginOneTwoThree,
                ),
                {_TestPluginRepositoryMixinTwo},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {_TestPluginRepositoryMixinTwo, _TestPluginRepositoryMixinThree},
            ),
            (
                (_TestPluginRepositoryPluginOneTwoThree,),
                {_TestPluginRepositoryMixinThree},
            ),
        ],
    )
    async def test_select_with_mixins(
        self,
        expected: Sequence[type[DummyPlugin]],
        mixins: set[
            _TestPluginRepositoryMixinOne
            | _TestPluginRepositoryMixinTwo
            | _TestPluginRepositoryMixinThree
        ],
    ) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginOne,
            _TestPluginRepositoryPluginOneTwo,
            _TestPluginRepositoryPluginOneTwoThree,
        )

        assert list(await sut.select(*mixins)) == list(expected)
