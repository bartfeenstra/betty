from collections.abc import AsyncIterator, Sequence
from typing import Self, Literal

import pytest
from typing_extensions import override

from betty.factory import Factory, new
from betty.machine_name import MachineName
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
)
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPlugin


class TestPluginNotFound:
    async def test_new(self) -> None:
        await PluginNotFound.new("my-first-plugin-id", StaticPluginRepository())


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


class _TestPluginRepositoryPluginDefaultFactory(DummyPlugin):
    pass


class _TestPluginRepositoryPluginCustomFactory(DummyPlugin):
    def __init__(self, must_be_true: Literal[True]):
        assert must_be_true

    @classmethod
    def new_custom(cls) -> Self:
        return cls(True)


class _TestPluginRepositoryPluginRepository(PluginRepository[DummyPlugin]):
    def __init__(
        self, *plugins: type[DummyPlugin], factory: Factory[DummyPlugin] | None = None
    ):
        super().__init__(factory=factory)
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

    async def test_new_with_default_factory(self) -> None:
        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginDefaultFactory
        )
        assert isinstance(
            await sut.new(_TestPluginRepositoryPluginDefaultFactory),
            _TestPluginRepositoryPluginDefaultFactory,
        )
        assert isinstance(
            await sut.new(_TestPluginRepositoryPluginDefaultFactory.plugin_id()),
            _TestPluginRepositoryPluginDefaultFactory,
        )

    async def test_new_with_custom_factory(self) -> None:
        async def factory(
            cls: type[DummyPlugin],
        ) -> DummyPlugin:
            return (
                cls.new_custom()
                if issubclass(cls, _TestPluginRepositoryPluginCustomFactory)
                else await new(cls)  # type: ignore[arg-type]
            )

        sut = _TestPluginRepositoryPluginRepository(
            _TestPluginRepositoryPluginCustomFactory, factory=factory
        )
        assert isinstance(
            await sut.new(_TestPluginRepositoryPluginCustomFactory),
            _TestPluginRepositoryPluginCustomFactory,
        )
        assert isinstance(
            await sut.new(_TestPluginRepositoryPluginCustomFactory.plugin_id()),
            _TestPluginRepositoryPluginCustomFactory,
        )
