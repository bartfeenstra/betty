import pytest

from betty.life_cycle import (
    AlreadyBootstrapped,
    AlreadyShutDown,
    Bootstrappable,
    LifeCycle,
    LifeCycleError,
    NotYetBootstrapped,
    Shutdownable,
)


class TestBootstrappable:
    async def test_assert_bootstrapped__not_yet_bootstrapped(self) -> None:
        with pytest.raises(NotYetBootstrapped):
            Bootstrappable().assert_bootstrapped()

    async def test_assert_bootstrapped__already_bootstrapped(self) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped__not_yet_bootstrapped(self) -> None:
        sut = Bootstrappable()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped__already_bootstrapped(
        self,
    ) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        with pytest.raises(LifeCycleError):
            sut.assert_not_bootstrapped()

    async def test_bootstrapped__not_yet_bootstrapped(self) -> None:
        assert not Bootstrappable().bootstrapped

    async def test_bootstrapped__already_bootstrapped(self) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        assert sut.bootstrapped

    async def test_bootstrap__not_yet_bootstrapped(self) -> None:
        await Bootstrappable().bootstrap()

    async def test_bootstrap__already_bootstrapped(self) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        with pytest.raises(AlreadyBootstrapped):
            await sut.bootstrap()


class TestShutdownable:
    async def test___del__(self) -> None:
        sut = Shutdownable()
        with pytest.warns(
            UserWarning,  # noqa: PT030
        ):
            del sut

    async def test_shutdown(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()

    async def test_shutdown__already_shut_down_wait(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        with pytest.raises(AlreadyShutDown):
            await sut.shutdown()

    async def test_shutdown__already_shut_down_no_wait(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        await sut.shutdown(wait=False)

    async def test_shut_down__not_yet_shut_down(self) -> None:
        sut = Shutdownable()
        assert not sut.shut_down
        await sut.shutdown()

    async def test_shut_down__already_shut_down(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        assert sut.shut_down

    async def test_assert_not_shut_down__not_yet_shut_down(self) -> None:
        sut = Shutdownable()
        sut.assert_not_shut_down()
        await sut.shutdown()

    async def test_assert_not_shut_down__already_shut_down(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        with pytest.raises(AlreadyShutDown):
            sut.assert_not_shut_down()


class TestLifeCycle:
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
