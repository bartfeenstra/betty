from collections.abc import AsyncIterator, Sequence

import pytest
from typing_extensions import override

from betty.locale.localizable import Localizable, plain
from betty.plugin import (
    PluginNotFound,
    Plugin,
    PluginRepository,
    validate_plugin_id,
    PluginId,
)


class TestValidatePluginId:
    @pytest.mark.parametrize(
        (
            "expected",
            "alleged_plugin_id",
        ),
        [
            (True, "package-plugin"),
            (False, "package_plugin"),
            (True, "package-module-plugin"),
            (False, "package_module_plugin"),
            (True, "plugin1234567890"),
            # String is exactly 255 characters.
            (
                True,
                "pluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginplug",
            ),
            # An empty string.
            (False, ""),
            # String exceeds 255 characters.
            (
                False,
                "pluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginpluginplugi",
            ),
        ],
    )
    async def test(self, expected: bool, alleged_plugin_id: str) -> None:
        assert validate_plugin_id(alleged_plugin_id) is expected


class TestPluginNotFound:
    async def test_new(self) -> None:
        PluginNotFound.new("my-first-plugin-id")


class TestPlugin:
    async def test_plugin_description(self) -> None:
        Plugin.plugin_description()


class _TestPluginRepositoryPluginBase(Plugin):
    @classmethod
    def plugin_id(cls) -> PluginId:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain(cls.__name__)  # pragma: no cover


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
    async def get(self, plugin_id: PluginId) -> type[_TestPluginRepositoryPluginBase]:
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
