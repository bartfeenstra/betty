"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.

Read more at :doc:`/development/plugin`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Self, overload, TYPE_CHECKING

from betty.error import UserFacingError
from betty.locale.localizable import _

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from betty.locale.localizable import Localizable
    from collections.abc import AsyncIterator, Sequence


class PluginError(UserFacingError):
    """
    Any error originating from the Plugin API.
    """

    pass


class Plugin(ABC):
    """
    A plugin.

    To test your own subclasses, use :py:class:`betty.test_utils.plugin.PluginTestBase`.
    """

    @classmethod
    @abstractmethod
    def plugin_id(cls) -> MachineName:
        """
        Get the plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        pass

    @classmethod
    @abstractmethod
    def plugin_label(cls) -> Localizable:
        """
        Get the human-readable short plugin label.
        """
        pass

    @classmethod
    def plugin_description(cls) -> Localizable | None:
        """
        Get the human-readable long plugin description.
        """
        return None


_PluginT = TypeVar("_PluginT", bound=Plugin)


class PluginNotFound(PluginError):
    """
    Raised when a plugin cannot be found.
    """

    @classmethod
    def new(cls, plugin_id: MachineName) -> Self:
        """
        Create a new instance.
        """
        return cls(
            _('Could not find a plugin "{plugin_id}".').format(plugin_id=plugin_id)
        )


_PluginMixinOneT = TypeVar("_PluginMixinOneT")
_PluginMixinTwoT = TypeVar("_PluginMixinTwoT")
_PluginMixinThreeT = TypeVar("_PluginMixinThreeT")


class PluginRepository(Generic[_PluginT], ABC):
    """
    Discover and manage plugins.
    """

    @abstractmethod
    async def get(self, plugin_id: MachineName) -> type[_PluginT]:
        """
        Get a single plugin by its ID.

        :raises PluginNotFound: if no plugin can be found for the given ID.
        """
        pass

    @overload
    async def select(self) -> Sequence[type[_PluginT]]:
        pass

    @overload
    async def select(
        self, mixin_one: type[_PluginMixinOneT]
    ) -> Sequence[type[_PluginT & _PluginMixinOneT]]:
        pass

    @overload
    async def select(
        self, mixin_one: type[_PluginMixinOneT], mixin_two: type[_PluginMixinTwoT]
    ) -> Sequence[type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT]]:
        pass

    @overload
    async def select(
        self,
        mixin_one: type[_PluginMixinOneT],
        mixin_two: type[_PluginMixinTwoT],
        mixin_three: type[_PluginMixinThreeT],
    ) -> Sequence[
        type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT & _PluginMixinThreeT]
    ]:
        pass

    async def select(
        self,
        mixin_one: type[_PluginMixinOneT] | None = None,
        mixin_two: type[_PluginMixinTwoT] | None = None,
        mixin_three: type[_PluginMixinThreeT] | None = None,
    ) -> (
        Sequence[type[_PluginT]]
        | Sequence[type[_PluginT & _PluginMixinOneT]]
        | Sequence[type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT]]
        | Sequence[
            type[_PluginT & _PluginMixinOneT & _PluginMixinTwoT & _PluginMixinThreeT]
        ]
    ):
        """
        Select a subset of the known plugins.

        When called without arguments, this returns all known plugins.
        When called with one or more arguments, this returns all known plugins
        that are also subclasses or **all** of the given mixins.

        This method is overloaded to provide for the majority use case of at most
        three mixins, because when using ``*args: *Ts``, we cannot unpack ``Ts`` into an
        :py:class:`basedtyping.Intersection` return type.
        """
        return [
            plugin
            async for plugin in self
            if self._select_plugin(plugin, mixin_one, mixin_two, mixin_three)
        ]

    def _select_plugin(
        self,
        plugin: type[_PluginT],
        mixin_one: type[_PluginMixinOneT] | None = None,
        mixin_two: type[_PluginMixinTwoT] | None = None,
        mixin_three: type[_PluginMixinThreeT] | None = None,
    ) -> bool:
        for mixin in (mixin_one, mixin_two, mixin_three):
            if mixin is None:
                continue
            if not issubclass(plugin, mixin):
                return False
        return True

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[type[_PluginT]]:
        pass
