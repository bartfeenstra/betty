import logging
import sys
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET, StreamHandler


class CliHandler(StreamHandler):
    COLOR_LEVELS = [
        (CRITICAL, 91),
        (ERROR, 91),
        (WARNING, 93),
        (INFO, 92),
        (DEBUG, 97),
        (NOTSET, 97),
    ]

    def __init__(self):
        StreamHandler.__init__(self, sys.stderr)

    def format(self, record: logging.LogRecord) -> str:
        s = StreamHandler.format(self, record)
        for level, color in self.COLOR_LEVELS:
            if record.levelno >= level:
                return self._color(s, color)

    def _color(self, s: str, color: int) -> str:
        return '\033[%dm%s\033[0m' % (color, s)
