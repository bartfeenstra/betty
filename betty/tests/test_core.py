import pytest
from betty.core import CoreComponent


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

    async def test_assert_bootstrapped(self) -> None:
        async with CoreComponent() as sut:
            sut.assert_bootstrapped()

    async def test_assert_bootstrapped_should_error_if_not_bootstrapped(self) -> None:
        sut = CoreComponent()
        with pytest.raises(RuntimeError), pytest.warns():
            sut.assert_bootstrapped()

    async def test_assert_not_bootstrapped(self) -> None:
        sut = CoreComponent()
        sut.assert_not_bootstrapped()

    async def test_assert_not_bootstrapped_should_error_if_bootstrapped(
        self,
    ) -> None:
        async with CoreComponent() as sut:
            with pytest.raises(RuntimeError), pytest.warns():
                sut.assert_not_bootstrapped()

    async def test_bootstrap(self) -> None:
        sut = CoreComponent()
        await sut.bootstrap()
        try:
            assert sut.bootstrapped
        finally:
            await sut.shutdown()

    async def test_bootstrapped(self) -> None:
        sut = CoreComponent()
        assert not sut.bootstrapped
        async with sut:
            assert sut.bootstrapped

    async def test_shutdown(self) -> None:
        sut = CoreComponent()
        await sut.bootstrap()
        await sut.shutdown()
        assert not sut.bootstrapped
