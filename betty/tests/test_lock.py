from unittest import TestCase

from betty.functools import sync
from betty.lock import Locks, AcquiredError


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
