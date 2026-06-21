"""
Logging utilities.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from asyncio import (
    CancelledError,
    get_running_loop,
    run_coroutine_threadsafe,
    to_thread,
)
from collections.abc import Callable, Coroutine
from functools import partial
from queue import Empty, Queue
from time import sleep
from typing import TYPE_CHECKING, final, override

from betty.functools import Result, ResultUnavailable, suppress
from betty.life_cycle.manage import ManagedLifeCycle

if TYPE_CHECKING:
    from betty.user import User


@final
class UserHandler(ManagedLifeCycle, logging.Handler):
    """
    Output log records through a :py:class`betty.user.User`.
    """

    def __init__(self, user: User, /):
        super().__init__()
        self._user = user
        self._result = Result(self._consume)
        self._thread = threading.Thread(
            name=self.__class__.__name__, target=suppress(self._result, BaseException)
        )
        self.life_cycle.on((self._thread.start, self._shutdown_thread))
        self._queue = Queue[Callable[[], Coroutine[None, None, None]]]()
        self._finish = threading.Event()
        self._loop = get_running_loop()

    async def _shutdown_thread(self, *, wait: bool = True) -> None:
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
        self._queue.put_nowait(partial(self._user.message_log, record))
