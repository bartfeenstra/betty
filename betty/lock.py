from typing import Hashable


class LockError:
    pass


class AcquiredError(LockError, RuntimeError):
    def __init__(self, resource: Hashable):
        super().__init__(f'Cannot acquire a lock for "{resource}", because it is locked already.')


class Locks:
    def __init__(self):
        self._locks = set[Hashable]()

    def acquire(self, resource: Hashable) -> None:
        if resource in self._locks:
            raise AcquiredError(resource)
        self._locks.add(resource)

    def release(self, resource: Hashable) -> None:
        self._locks.discard(resource)
