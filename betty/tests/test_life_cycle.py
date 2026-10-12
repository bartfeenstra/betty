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

    async def test_is_bootstrapped__not_yet_bootstrapped(self) -> None:
        assert not Bootstrappable().is_bootstrapped

    async def test_is_bootstrapped__already_bootstrapped(self) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        assert sut.is_bootstrapped

    async def test_bootstrap__not_yet_bootstrapped(self) -> None:
        await Bootstrappable().bootstrap()

    async def test_bootstrap__already_bootstrapped(self) -> None:
        sut = Bootstrappable()
        await sut.bootstrap()
        with pytest.raises(AlreadyBootstrapped):
            await sut.bootstrap()

    async def test___aenter__(self) -> None:
        async with Bootstrappable() as sut:
            assert sut.is_bootstrapped


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

    async def test_shutdown__already_shutdown_wait(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        with pytest.raises(AlreadyShutDown):
            await sut.shutdown()

    async def test_shutdown__already_shutdown_no_wait(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        await sut.shutdown(wait=False)

    async def test_is_shutdown__not_yet_shutdown(self) -> None:
        sut = Shutdownable()
        assert not sut.is_shutdown
        await sut.shutdown()

    async def test_is_shutdown__already_shutdown(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        assert sut.is_shutdown

    async def test_assert_not_shutdown__not_yet_shutdown(self) -> None:
        sut = Shutdownable()
        sut.assert_not_shutdown()
        await sut.shutdown()

    async def test_assert_not_shutdown__already_shutdown(self) -> None:
        sut = Shutdownable()
        await sut.shutdown()
        with pytest.raises(AlreadyShutDown):
            sut.assert_not_shutdown()

    async def test___aexit__(self) -> None:
        async with Shutdownable() as sut:
            pass
        assert sut.is_shutdown


class TestLifeCycle:
    async def test___aenter__(self) -> None:
        async with LifeCycle() as sut:
            assert sut.is_bootstrapped

    async def test___aexit__(self) -> None:
        async with LifeCycle() as sut:
            pass
        assert sut.is_bootstrapped
        assert sut.is_shutdown

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

    async def test_alive__shutdown(self) -> None:
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

    async def test_assert_alive__shutdown(self) -> None:
        async with LifeCycle() as sut:
            pass
        with pytest.raises(AlreadyShutDown):
            sut.assert_alive()
