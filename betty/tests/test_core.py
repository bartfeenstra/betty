from typing_extensions import override

import pytest
from betty.core import CoreComponent, Bootstrapped, ShutdownStack, Shutdownable


class TestBootstrapped:
    class _DummyBootstrapped(Bootstrapped):
        def set_bootstrapped(self, bootstrapped: bool) -> None:
            self._bootstrapped = bootstrapped

    async def test_assert_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        with pytest.raises(RuntimeError):
            sut.assert_bootstrapped()
        sut.set_bootstrapped(True)
        sut.assert_bootstrapped()

    async def test_assert_bootstrapped_should_error_if_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        with pytest.raises(RuntimeError), pytest.warns():
            sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped_should_error_if_bootstrapped(
        self,
    ) -> None:
        sut = self._DummyBootstrapped()
        sut.set_bootstrapped(True)
        with pytest.raises(RuntimeError), pytest.warns():
            sut.assert_not_bootstrapped()

    async def test_bootstrapped(self) -> None:
        sut = self._DummyBootstrapped()
        assert not sut.bootstrapped
        sut.set_bootstrapped(True)
        assert sut.bootstrapped


class TestShutdownStack:
    @pytest.mark.parametrize(
        "expected_wait",
        [
            True,
            False,
        ],
    )
    async def test_shutdown(self, expected_wait: bool) -> None:
        carrier = []

        async def _shutdown(*, wait: bool) -> None:
            nonlocal carrier
            carrier.append(wait)

        class _Shutdownable(Shutdownable):
            @override
            async def shutdown(self, *, wait: bool = True) -> None:
                nonlocal carrier
                carrier.append(wait)

        sut = ShutdownStack()
        sut.append(_shutdown)
        sut.append(_Shutdownable())
        await sut.shutdown(wait=expected_wait)
        assert carrier == [expected_wait, expected_wait]

    async def test_shutdown_without_callbacks_without_wait(self) -> None:
        sut = ShutdownStack()
        await sut.shutdown(wait=False)

    async def test_shutdown_without_callbacks_with_wait(self) -> None:
        sut = ShutdownStack()
        await sut.shutdown(wait=True)


class TestCoreComponent:
    async def test___aenter__(self) -> None:
        async with CoreComponent() as sut:
            assert sut.bootstrapped

    async def test___aexit__(self) -> None:
        async with CoreComponent() as sut:
            pass
        assert not sut.bootstrapped

    async def test___del__(self) -> None:
        sut = CoreComponent()
        await sut.bootstrap()
        with pytest.warns():
            del sut

    async def test_bootstrap(self) -> None:
        sut = CoreComponent()
        await sut.bootstrap()
        try:
            assert sut.bootstrapped
        finally:
            await sut.shutdown()

    async def test_shutdown(self) -> None:
        sut = CoreComponent()
        await sut.bootstrap()
        await sut.shutdown()
        assert not sut.bootstrapped
