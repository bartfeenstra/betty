import logging
import time
from math import ceil
from types import TracebackType
from typing import Self

from babel.dates import format_timedelta

from betty.typing import internal


@internal
class Timer:
    def __init__(self, message: str):
        self._message = message
        self._start: int | None = None
        self._end: int | None = None

    @property
    def duration(self) -> int:
        return (self._end or time.monotonic_ns()) - (self._start or 0)

    def start(self) -> None:
        self._start = time.monotonic_ns()
        logging.getLogger().debug(f"{self._message}...")

    def stop(self) -> None:
        self._end = time.monotonic_ns()
        logging.getLogger().debug(
            f"{self._message} (finished in {format_timedelta(ceil(self.duration /10**9))})"
        )

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.stop()
