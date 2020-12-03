from betty.asyncio import sync
from betty.lock import Locks, AcquiredError
from betty.tests import TestCase


class LocksTest(TestCase):
    @sync
    async def test_acquire(self):
        resource = 999
        sut = Locks()
        sut.acquire(resource)
        with self.assertRaises(AcquiredError):
            sut.acquire(resource)

    @sync
    async def test_release(self):
        resource = 999
        sut = Locks()
        sut.acquire(resource)
        sut.release(resource)
        sut.acquire(resource)
