from __future__ import annotations

from concurrent.futures._base import Executor, wait, Future
from typing import Any, Iterator, Callable, TypeVar, Iterable, ParamSpec

T = TypeVar('T')
U = TypeVar('U')
P = ParamSpec('P')


class ExceptionRaisingAwaitableExecutor(Executor):
    def __init__(self, executor: Executor):
        self._executor = executor
        self._awaitables: list[Future[Any]] = []

    def submit(self, task: Callable[P, T], /, *args: P.args, **kwargs: P.kwargs) -> Future[T]:
        future = self._executor.submit(task, *args, **kwargs)
        self._awaitables.append(future)
        return future

    def map(
        self,
        task: Callable[[U], T],
        *values: Iterable[U],
        timeout: int | float | None = None,
        chunksize: int = 1,
    ) -> Iterator[T]:
        return self._executor.map(task, *values, timeout=timeout, chunksize=chunksize)

    def wait(self) -> None:
        awaitables = self._awaitables
        self._awaitables = []
        wait(awaitables)

    def shutdown(self, *args: Any, **kwargs: Any) -> None:
        self._executor.shutdown(*args, **kwargs)
        for future in self._awaitables:
            future.result()
