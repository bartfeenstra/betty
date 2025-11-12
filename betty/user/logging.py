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
from typing import final

from typing_extensions import override

from betty.functools import Result, ResultUnavailable, suppress
from betty.user import User


@final
class UserHandler(logging.Handler):
    """
    Output log records through a :py:class`betty.user.User`.
    """

    def __init__(self, user: User):
        super().__init__()
        self._started = False
        self._user = user
        self._result = Result(self._consume)
        self._thread = threading.Thread(
            name=self.__class__.__name__, target=suppress(self._result, BaseException)
        )
        self._queue = Queue[Callable[[], Awaitable[None]]]()
        self._finish = threading.Event()
        self._loop = get_running_loop()

    async def start(self) -> None:
        """
        Start the handler.
        """
        if not self._started:
            self._started = True
            self._thread.start()

    async def stop(self) -> None:
        """
        Stop the handler.
        """
        if not self._started:
            return
        self._finish.set()
        with contextlib.suppress(CancelledError):
            await to_thread(self._thread.join)
        # If no log messages were recorded, there is no result.
        with contextlib.suppress(ResultUnavailable):
            self._result.result()
        self._started = False

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
        self._queue.put_nowait(partial(self._user.message_log, record))
