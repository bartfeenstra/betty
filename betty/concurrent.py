from concurrent.futures._base import Executor


class ExceptionRaisingExecutor(Executor):
    def __init__(self, executor: Executor):
        self._executor = executor
        self._futures = []

    def submit(self, *args, **kwargs):
        future = self._executor.submit(*args, **kwargs)
        self._futures.append(future)
        return future

    def map(self, *args, **kwargs):
        return self._executor.map(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        self._executor.shutdown(*args, **kwargs)
        for future in self._futures:
            future.result()
