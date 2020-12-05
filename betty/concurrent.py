from concurrent.futures import Executor


class ExceptionRaisingExecutor(Executor):
    """
    Raise task exeptions in the current thread.

    Decorate another executor, and ensure any exceptions raised by tasks will be raised within the current thread.
    """

    def __init__(self, executor: Executor):
        """
        Initialize a new instance.

        Parameters
        ----------
        executor: concurrent.futures.Executor
            The executor to decorate, and that will be responsible for executing the tasks.

        """
        self._executor = executor
        self._futures = []

    def submit(self, *args, **kwargs):
        """
        """
        future = self._executor.submit(*args, **kwargs)
        self._futures.append(future)
        return future

    def map(self, *args, **kwargs):
        """
        """
        return self._executor.map(*args, **kwargs)

    def shutdown(self, *args, **kwargs):
        self._executor.shutdown(*args, **kwargs)
        for future in self._futures:
            future.result()
