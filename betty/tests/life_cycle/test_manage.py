import pytest

from betty.life_cycle import (
    AlreadyBootstrapped,
    AlreadyShutDown,
    LifeCycle,
)
from betty.life_cycle.manage import LifeCycleManager, ManagedLifeCycle


class TestManagedLifeCycle:
    async def test_bootstrap(self) -> None:
        carrier = []
        sut = ManagedLifeCycle()
        sut.life_cycle.on_bootstrap(lambda: carrier.append(True))
        await sut.bootstrap()
        await sut.shutdown()
        assert carrier == [True]

    def test_life_cycle(self) -> None:
        sut = ManagedLifeCycle()
        assert sut.life_cycle

    @pytest.mark.parametrize(
        "wait",
        [
            True,
            False,
        ],
    )
    async def test_shutdown(self, wait: bool) -> None:
        carrier = []
        sut = ManagedLifeCycle()
        sut.life_cycle.on_shutdown(lambda wait: carrier.append(wait))
        await sut.bootstrap()
        await sut.shutdown(wait=wait)
        assert carrier == [wait]


class TestLifeCycleManager:
    async def test_synchronize__not_yet_bootstrapped(self) -> None:
        sut = LifeCycleManager()
        other = LifeCycle()
        await sut.synchronize(other)
        async with sut:
            assert other.bootstrapped
        assert other.shut_down

    async def test_synchronize__self_not_yet_bootstrapped_other_bootstrapped(
        self,
    ) -> None:
        sut = LifeCycleManager()
        async with LifeCycle() as other:
            with pytest.raises(AlreadyBootstrapped):
                await sut.synchronize(other)

    async def test_synchronize__self_bootstrapped_other_not_yet_bootstrapped(
        self,
    ) -> None:
        async with LifeCycleManager() as sut:
            other = LifeCycle()
            await sut.synchronize(other)
            assert other.bootstrapped
        assert other.shut_down

    async def test_synchronize__self_shut_down(self) -> None:
        async with LifeCycleManager() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            await sut.synchronize(LifeCycle())

    async def test_synchronize__other_shut_down(self) -> None:
        async with LifeCycleManager() as sut:
            async with LifeCycle() as other:
                pass
            with pytest.raises(AlreadyShutDown):
                await sut.synchronize(other)

    async def test_bootstrap(self) -> None:
        sut = LifeCycleManager()
        await sut.bootstrap()
        await sut.shutdown()

    @pytest.mark.parametrize(
        "wait",
        [
            True,
            False,
        ],
    )
    async def test_on(self, wait: bool) -> None:
        carrier = []
        sut = LifeCycleManager()
        sut.on((lambda: carrier.append(True), lambda wait: carrier.append(wait)))
        await sut.bootstrap()
        assert carrier == [True]
        await sut.shutdown(wait=wait)
        assert carrier == [True, wait]

    async def test_on__bootstrapped(self) -> None:
        async with LifeCycleManager() as sut:
            with pytest.raises(AlreadyBootstrapped):
                sut.on((lambda: None, lambda wait: None))

    async def test_on_bootstrap(self) -> None:
        carrier = []
        sut = LifeCycleManager()
        sut.on_bootstrap(lambda: carrier.append(True))
        async with sut:
            assert carrier == [True]

    async def test_on_bootstrap__bootstrapped(self) -> None:
        async with LifeCycleManager() as sut:
            with pytest.raises(AlreadyBootstrapped):
                sut.on_bootstrap(lambda: None)

    @pytest.mark.parametrize(
        "wait",
        [
            True,
            False,
        ],
    )
    async def test_on_shutdown(self, wait: bool) -> None:
        carrier = []
        sut = LifeCycleManager()
        sut.on_shutdown(lambda wait: carrier.append(wait))
        await sut.bootstrap()
        assert not carrier
        await sut.shutdown(wait=wait)
        assert carrier == [wait]

    async def test_on_shutdown__shut_down(self) -> None:
        async with LifeCycleManager() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            sut.on_shutdown(lambda wait: None)

    async def test_shutdown(self) -> None:
        sut = LifeCycleManager()
        await sut.bootstrap()
        await sut.shutdown()
