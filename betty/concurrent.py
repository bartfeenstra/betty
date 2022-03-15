from concurrent.futures._base import Executor, wait


class ExceptionRaisingAwaitableExecutor(Executor):
    def __init__(self, executor: Executor):
        self._executor = executor
        self._awaitables = []

    def submit(self, *args, **kwargs):
        future = self._executor.submit(*args, **kwargs)
        self._awaitables.append(future)
        return future

    def map(self, *args, **kwargs):
        return self._executor.map(*args, **kwargs)

    def wait(self) -> None:
        awaitables = self._awaitables
        self._awaitables = []
        wait(awaitables)

    def shutdown(self, *args, **kwargs):
        self._executor.shutdown(*args, **kwargs)
        for future in self._awaitables:
            future.result()
