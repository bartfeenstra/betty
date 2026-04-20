"""
Life cycle management.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Any, final, override

from betty.asyncio import resolve_await
from betty.life_cycle import (
    Bootstrappable,
    Bootstrapper,
    LifeCycle,
    Shutdownable,
    Shutdowner,
)

if TYPE_CHECKING:
    from collections.abc import Collection, MutableSequence


class ManagedLifeCycle(LifeCycle):
    """
    An object that can bootstrap and shut down, and manage resources upon these events.

    Subclasses and third party code can manage resources using the
    :py:attr:`~betty.life_cycle.manage.ManagedLifeCycle.life_cycle` property, which ensures everything is done in order.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.__life_cycle = LifeCycleManager()
        super().__init__(*args, **kwargs)

    @final
    @property
    def life_cycle(self) -> LifeCycleManager:
        """
        The life cycle manager.
        """
        return self.__life_cycle

    @final
    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        try:
            await self.life_cycle.bootstrap()
        except BaseException:
            await self.shutdown(wait=False)
            raise

    @final
    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        await super().shutdown(wait=wait)
        await self.__life_cycle.shutdown(wait=wait)


@final
class LifeCycleManager(LifeCycle):
    """
    A life cycle manager.
    """

    def __init__(self):
        super().__init__()
        self._bootstrappers: MutableSequence[Collection[Bootstrapper]] = []
        self._shutdowners: MutableSequence[Collection[Shutdowner]] = []

    @override
    async def bootstrap(self) -> None:
        await super().bootstrap()
        for bootstrappers in self._bootstrappers:
            await gather(*[
                resolve_await(bootstrapper()) for bootstrapper in bootstrappers
            ])

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        await super().shutdown(wait=wait)
        for shutdowners in self._shutdowners:
            await gather(*[
                resolve_await(shutdowner(wait=wait)) for shutdowner in shutdowners
            ])

    async def synchronize(self, *life_cycles: Bootstrappable | Shutdownable) -> None:
        """
        Attach a batch of other life cycles to this one, and ensure they are all synchronized.

        The life cycles within the batch will be bootstrapped and shut down concurrently.
        """
        self.assert_not_shut_down()
        shutdowners = []
        for life_cycle in life_cycles:
            if isinstance(life_cycle, Shutdownable):
                life_cycle.assert_not_shut_down()
                shutdowners.append(life_cycle.shutdown)
        if self.bootstrapped:
            await gather(*[
                life_cycle.bootstrap()
                for life_cycle in life_cycles
                if isinstance(life_cycle, Bootstrappable)
            ])
        else:
            bootstrappers = []
            for life_cycle in life_cycles:
                if isinstance(life_cycle, Bootstrappable):
                    life_cycle.assert_not_bootstrapped()
                    bootstrappers.append(life_cycle.bootstrap)
            self._bootstrappers.append(bootstrappers)
        self._shutdowners.append(shutdowners)

    def on_bootstrap(self, *bootstrappers: Bootstrapper) -> None:
        """
        Add a batch of bootstrap callbacks.

        The callbacks within the batch will be invoked concurrently.
        """
        self.assert_not_bootstrapped()
        if not bootstrappers:
            return
        self._bootstrappers.append(bootstrappers)

    def on_shutdown(self, *shutdowners: Shutdowner) -> None:
        """
        Add a batch of shutdown callbacks.

        The callbacks within the batch will be invoked concurrently.
        """
        self.assert_not_shut_down()
        if not shutdowners:
            return
        self._shutdowners.append(shutdowners)

    def on(self, *callbacks: tuple[Bootstrapper, Shutdowner]) -> None:
        """
        Add a batch of callbacks.

        The callbacks within the batch will be invoked concurrently.
        """
        bootstrappers, shutdowners = list(zip(*callbacks, strict=False))
        self.on_bootstrap(*bootstrappers)
        self.on_shutdown(*shutdowners)
