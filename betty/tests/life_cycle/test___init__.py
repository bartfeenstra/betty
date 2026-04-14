import pytest

from betty.life_cycle import (
    AlreadyBootstrapped,
    AlreadyShutDown,
    LifeCycle,
    LifeCycleError,
    NotYetBootstrapped,
)


class TestLifeCycle:
    async def test_assert_bootstrapped__not_yet_bootstrapped(self) -> None:
        with pytest.raises(NotYetBootstrapped):
            LifeCycle().assert_bootstrapped()

    async def test_assert_bootstrapped__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            sut.assert_bootstrapped()

    async def test_assert_bootstrapped__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped__bootstrapped(
        self,
    ) -> None:
        async with LifeCycle() as sut:
            with pytest.raises(LifeCycleError):
                sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped__shut_down(
        self,
    ) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(LifeCycleError):
            sut.assert_not_bootstrapped()

    async def test_bootstrapped__not_yet_bootstrapped(self) -> None:
        assert not LifeCycle().bootstrapped

    async def test_bootstrapped__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            assert sut.bootstrapped

    async def test_bootstrapped__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        assert sut.bootstrapped

    async def test___aenter__(self) -> None:
        async with LifeCycle() as sut:
            assert sut.bootstrapped

    async def test___aexit__(self) -> None:
        async with LifeCycle() as sut:
            pass
        assert sut.bootstrapped
        assert sut.shut_down

    async def test___del__(self) -> None:
        sut = LifeCycle()
        await sut.bootstrap()
        with pytest.warns(
            UserWarning,  # noqa: PT030
        ):
            del sut

    async def test_bootstrap__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        await sut.bootstrap()
        try:
            assert sut.bootstrapped
        finally:
            await sut.shutdown()
        assert sut.shut_down

    async def test_bootstrap__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            with pytest.raises(AlreadyBootstrapped):
                await sut.bootstrap()

    async def test_bootstrap__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(AlreadyBootstrapped):
            await sut.bootstrap()

    async def test_shutdown(self) -> None:
        sut = LifeCycle()
        await sut.bootstrap()
        await sut.shutdown()
        assert sut.shut_down

    async def test_shutdown__already_shut_down_wait(self) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            await sut.shutdown()

    async def test_shutdown__already_shut_down_no_wait(self) -> None:
        async with LifeCycle() as sut:
            pass
        await sut.shutdown(wait=False)

    async def test_shut_down(self) -> None:
        sut = LifeCycle()
        await sut.bootstrap()
        await sut.shutdown()
        assert sut.shut_down

    def test_shut_down__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        assert not sut.shut_down

    async def test_shut_down__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            assert not sut.shut_down

    def test_assert_not_shut_down__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        sut.assert_not_shut_down()

    async def test_assert_not_shut_down__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            sut.assert_not_shut_down()

    async def test_assert_not_shut_down__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            sut.assert_not_shut_down()

    def test_alive__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        assert not sut.alive

    async def test_alive__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            assert sut.alive

    async def test_alive__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        assert not sut.alive

    def test_assert_alive__not_yet_bootstrapped(self) -> None:
        sut = LifeCycle()
        with pytest.raises(NotYetBootstrapped):
            sut.assert_alive()

    async def test_assert_alive__bootstrapped(self) -> None:
        async with LifeCycle() as sut:
            sut.assert_alive()

    async def test_assert_alive__shut_down(self) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            sut.assert_alive()
