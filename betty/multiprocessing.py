"""
Multiprocessing functionality.
"""

from concurrent import futures
from multiprocessing import get_context
from signal import SIG_IGN, SIGINT, signal

CONTEXT = get_context("spawn")


class ProcessPoolExecutor(futures.ProcessPoolExecutor):
    """
    Like :py:class:`concurrent.futures.ProcessPoolExecutor`, but with error handling and low memory consumption.

    This
    - uses the ``spawn`` method to create new processes, which is the Python 3.14 default.
    - ignores SIGINT/:py:class:`KeyboardInterrupt` delivered to it by the parent process to prevent unhelpful
      additional :py:class:`KeyboardInterrupt` being raised from within the process pool.
    """

    def __init__(
        self, max_workers: int | None = None, *, max_tasks_per_child: int | None = None
    ):
        super().__init__(
            initializer=signal,
            initargs=(SIGINT, SIG_IGN),
            max_workers=max_workers,
            max_tasks_per_child=max_tasks_per_child,
            mp_context=CONTEXT,
        )
