from concurrent.futures._base import Executor
from typing import Callable


class JoiningError(RuntimeError):
    def __init__(self):
        super().__init__('This scheduler is currently joining.')


class Scheduler:
    async def schedule(self, task: Callable, *args, **kwargs) -> None:
        raise NotImplementedError

    async def join(self) -> None:
        raise NotImplementedError


class ExecutorScheduler(Scheduler):
    def __init__(self, executor: Executor):
        self._joining = False
        self._executor = executor

    async def schedule(self, task: Callable, *args, **kwargs) -> None:
        if self._joining:
            raise JoiningError()
        self._executor.submit(task, *args, **kwargs)

    async def join(self) -> None:
        if self._joining:
            raise JoiningError()
        self._joining = True
        self._executor.shutdown()
