from collections.abc import AsyncIterator, Sequence

import pytest
from typing_extensions import override

from betty.locale.localizable import Localizable, static
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
)
from betty.machine_name import MachineName


class TestPluginNotFound:
    async def test_new(self) -> None:
        PluginNotFound.new("my-first-plugin-id")


class TestPlugin:
    async def test_plugin_description(self) -> None:
        Plugin.plugin_description()


class _TestPluginRepositoryPluginBase(Plugin):
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return static(cls.__name__)  # pragma: no cover


class _TestPluginRepositoryMixinOne:
    pass


class _TestPluginRepositoryMixinTwo:
    pass


class _TestPluginRepositoryMixinThree:
    pass


class _TestPluginRepositoryPluginOne(
    _TestPluginRepositoryPluginBase, _TestPluginRepositoryMixinOne
):
    pass


class _TestPluginRepositoryPluginOneTwo(
    _TestPluginRepositoryPluginBase,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
):
    pass


class _TestPluginRepositoryPluginOneTwoThree(
    _TestPluginRepositoryPluginBase,
    _TestPluginRepositoryMixinOne,
    _TestPluginRepositoryMixinTwo,
    _TestPluginRepositoryMixinThree,
):
    pass


class _TestPluginRepositoryPluginRepository(
    PluginRepository[_TestPluginRepositoryPluginBase]
):
    def __init__(self, *plugins: type[_TestPluginRepositoryPluginBase]):
        self._plugins = {plugin.plugin_id(): plugin for plugin in plugins}

    @override
    async def get(
        self, plugin_id: MachineName
    ) -> type[_TestPluginRepositoryPluginBase]:
        return self._plugins[plugin_id]

    @override
    async def __aiter__(self) -> AsyncIterator[type[_TestPluginRepositoryPluginBase]]:
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
        expected: Sequence[type[_TestPluginRepositoryPluginBase]],
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
