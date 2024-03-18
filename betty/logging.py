"""
Provide logging utilities.
"""
import logging
import sys
from collections.abc import Callable
from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET, StreamHandler, LogRecord, Filter, Handler
from types import TracebackType
from typing import Any, Self, Mapping

from betty.locale import Localizable, Localizer


class Logger(logging.Logger):
    def __init__(self, logger: logging.Logger, localizer: Localizer):
        self._logger = logger
        self._localizer = localizer

    def _localize(self, msg: object) -> object:
        if isinstance(msg, Localizable):
            return msg.localize(self._localizer)
        return msg

    def addFilter(self, filter: Filter | Callable[[LogRecord], LogRecord | bool]) -> None:
        self._logger.addFilter(filter)

    def removeFilter(self, filter: Filter | Callable[[LogRecord], LogRecord | bool]) -> None:
        self._logger.removeFilter(filter)

    def filter(self, record: LogRecord) -> LogRecord | bool:
        return self._logger.filter(record)

    def setLevel(self, level: int | str) -> None:
        self._logger.setLevel(level)

    def debug(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.debug(self._localize(msg), *args, **kwargs)

    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.info(self._localize(msg), *args, **kwargs)

    def warning(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.warning(self._localize(msg), *args, **kwargs)

    def warn(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.warn(self._localize(msg), *args, **kwargs)

    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.error(self._localize(msg), *args, **kwargs)

    def exception(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(self._localize(msg), *args, **kwargs)

    def critical(self, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.critical(self._localize(msg), *args, **kwargs)

    def log(self, level: int, msg: object, *args: Any, **kwargs: Any) -> None:
        self._logger.log(level, self._localize(msg), *args, **kwargs)

    def findCaller(self, stack_info: bool = False, stacklevel: int = 1) -> tuple[str, int, str, str | None]:
        return self._logger.findCaller(stack_info, stacklevel)

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: tuple[object, ...] | Mapping[str, object],
        exc_info: tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None] | None = None,
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None,
    ) -> LogRecord:
        return self._logger.makeRecord(name, level, fn, lno, self._localize(msg), args, exc_info, func, extra, sinfo)

    def handle(self, record: LogRecord) -> None:
        self._logger.handle(record)

    def addHandler(self, hdlr: Handler) -> None:
        self._logger.addHandler(hdlr)

    def removeHandler(self, hdlr: Handler) -> None:
        self._logger.removeHandler(hdlr)

    def hasHandlers(self) -> bool:
        return self._logger.hasHandlers()

    def callHandlers(self, record: LogRecord) -> None:
        return self._logger.callHandlers(record)

    def getEffectiveLevel(self) -> int:
        return self._logger.getEffectiveLevel()

    def isEnabledFor(self, level: int) -> bool:
        return self._logger.isEnabledFor(level)

    def getChild(self, suffix: str) -> Self:
        return type(self)(self._logger.getChild(suffix), self._localizer)

    def getChildren(self) -> set[logging.Logger]:
        return self._logger.getChildren()


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
