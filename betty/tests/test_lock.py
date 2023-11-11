import pytest

from betty.lock import Locks, AcquiredError


class TestLocks:
    async def test_acquire(self) -> None:
        resource = 999
        sut = Locks()
        sut.acquire(resource)
        with pytest.raises(AcquiredError):
            sut.acquire(resource)

    async def test_release(self) -> None:
        resource = 999
        sut = Locks()
        sut.acquire(resource)
        sut.release(resource)
        sut.acquire(resource)
