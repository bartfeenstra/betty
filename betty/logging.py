"""
Provide logging utilities.
"""
import sys
from collections import defaultdict
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET, StreamHandler, LogRecord, Handler


class CliHandler(
    StreamHandler,  # type: ignore[type-arg]
):
    COLOR_LEVELS = {
        CRITICAL: 91,
        ERROR: 91,
        WARNING: 93,
        INFO: 92,
        DEBUG: 97,
        NOTSET: 97,
    }

    def __init__(self):
        StreamHandler.__init__(self, sys.stderr)

    def format(self, record: LogRecord) -> str:
        s = StreamHandler.format(self, record)
        for level, color in self.COLOR_LEVELS.items():
            if record.levelno >= level:
                return self._color(s, color)
        return self._color(s, self.COLOR_LEVELS[NOTSET])

    def _color(self, s: str, color: int) -> str:
        return '\033[%dm%s\033[0m' % (color, s)


class CatchHandler(Handler):
    def __init__(self) -> None:
        super().__init__()
        self._catches = defaultdict(list)

    def handle(self, record: LogRecord) -> None:
        self._catches[record.levelno].append(record)
