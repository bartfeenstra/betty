"""
Logging utilities.
"""

import contextlib
import logging
import threading
from asyncio import (
    CancelledError,
    get_running_loop,
    run_coroutine_threadsafe,
    to_thread,
)
from collections.abc import Awaitable, Callable
from functools import partial
from queue import Empty, Queue
from time import sleep
from types import TracebackType
from typing import Self, final

from typing_extensions import override

from betty.functools import Result, ResultUnavailable, suppress
from betty.locale.localizable import plain
from betty.user import User


@final
class UserHandler(logging.Handler):
    """
    Output log records through a :py:class`betty.user.User`.
    """

    def __init__(self, user: User):
        super().__init__(-1)
        self._user = user
        self._result = Result(self._consume)
        self._thread = threading.Thread(
            name=self.__class__.__name__, target=suppress(self._result, BaseException)
        )
        self._queue = Queue[Callable[[], Awaitable[None]]]()
        self._finish = threading.Event()
        self._loop = get_running_loop()

    async def __aenter__(self) -> Self:
        self._thread.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._finish.set()
        with contextlib.suppress(CancelledError):
            await to_thread(self._thread.join)
        # If no log messages were recorded, there is no result.
        with contextlib.suppress(ResultUnavailable):
            self._result.result()

    def _consume(self) -> None:
        final_iteration = False
        while True:
            try:
                task = self._queue.get_nowait()
            except Empty:
                if self._finish.is_set():
                    # Perform one final iteration to account for race conditions between the finish event being set and
                    # the final tasks being added to the queue.
                    if final_iteration:
                        return
                    final_iteration = True
                # Sleep to prevent the loop from taking up CPU time when the queue is empty.
                sleep(0.001)
            else:
                run_coroutine_threadsafe(task(), self._loop).result()

    @override
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            message_func = self._user.message_error
        elif record.levelno >= logging.WARNING:
            message_func = self._user.message_warning
        elif record.levelno >= logging.INFO:
            message_func = self._user.message_information
        else:
            message_func = self._user.message_debug
        self._queue.put_nowait(partial(message_func, plain(self.format(record))))
