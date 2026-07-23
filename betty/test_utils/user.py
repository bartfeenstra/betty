"""
Test utilities for :py:mod:`betty.user`.
"""

from __future__ import annotations

import logging
import sys
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final, final, overload, override

from betty.localizer import Localizer, default_localizer
from betty.nothing import Nothing, NothingType
from betty.progresses.no_op import NoOpProgress
from betty.user import Severity, User, UserTimeoutError

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Collection,
        Iterable,
        Mapping,
        MutableSequence,
    )

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.progress import Progress


@final
class StaticUser(User):
    """
    A static user with predefined responses.
    """

    localizer: Final[Localizer] = default_localizer

    def __init__(
        self,
        *,
        confirmations: Iterable[bool | None] = (),
        inputs: Iterable[str | None] = (),
        severity: Severity | bool = User.default_severity,
    ):
        self._confirmations = iter(confirmations)
        self._inputs = iter(inputs)
        self._exceptions: MutableSequence[BaseException] = []
        self._messages: Mapping[Severity, MutableSequence[ResolvableLocalizable]] = (
            defaultdict(list)
        )
        self._logs: MutableSequence[logging.LogRecord] = []
        self._log_formatter = logging.Formatter()
        self.severity = severity

    def _format_fragments(self, fragments: str | Iterable[str]) -> str:
        if isinstance(fragments, str):
            fragments = [fragments]
        return ", ".join(f'"{fragment}"' for fragment in fragments)

    def _contains_fragments(self, message: str, fragments: Iterable[str]) -> bool:
        return all(fragment in message for fragment in fragments)

    def _assert_message(
        self,
        fragments: str | Iterable[str],
        message_kind: str,
        messages: Collection[str],
    ) -> None:
        if isinstance(fragments, str):
            fragments = [fragments]
        for message in messages:
            if self._contains_fragments(message, fragments):
                return
        raise AssertionError(
            f"Failed asserting that {message_kind} was sent containing the fragment(s) {self._format_fragments(fragments)}."
        )

    def assert_exception(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that an exception message was sent.
        """
        self._assert_message(
            fragments, "an exception", list(map(str, self._exceptions))
        )

    def assert_message(
        self, fragments: str | Iterable[str], severity: Severity, /
    ) -> None:
        """
        Assert that an error message was sent.
        """
        self._assert_message(
            fragments,
            f"a(n) {severity.name} message",
            [
                default_localizer.localize(message)
                for message in self._messages[severity]
            ],
        )

    def assert_log(self, fragments: str | Iterable[str], /) -> None:
        """
        Assert that a log message was sent.
        """
        self._assert_message(
            fragments, "a log record", list(map(self._log_formatter.format, self._logs))
        )

    def _assert_fragments(
        self,
        fragments: str | Iterable[str],
        message_kind: str,
        messages: Collection[str],
    ) -> None:
        if isinstance(fragments, str):
            fragments = [fragments]
        for message in messages:
            if self._contains_fragments(message, fragments):
                raise AssertionError(
                    f'Failed asserting that "{message_kind}" was sent containing the fragment(s) {self._format_fragments(fragments)}.'
                )

    def assert_not_exception(self, fragments: str | Iterable[str], /) -> None:
        """
        Assert that no exception message was sent.
        """
        self._assert_fragments(fragments, "exception", list(map(str, self._exceptions)))

    def assert_not_message(
        self, fragments: str | Iterable[str], severity: Severity, /
    ) -> None:
        """
        Assert that a given message was not sent.
        """
        self._assert_fragments(
            fragments,
            f"a(n) {severity.name} message",
            [
                default_localizer.localize(message)
                for message in self._messages[severity]
            ],
        )

    def assert_not_log(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no log message was sent.
        """
        self._assert_fragments(
            fragments, "log", list(map(self._log_formatter.format, self._logs))
        )

    @override
    async def exception(self) -> None:
        exception = sys.exception()
        assert exception
        self._exceptions.append(exception)

    @override
    async def message(
        self, message: ResolvableLocalizable, severity: Severity, /
    ) -> None:
        self._messages[severity].append(message)

    @override
    async def log(self, record: logging.LogRecord, /) -> None:
        self._logs.append(record)

    @override
    @asynccontextmanager
    async def progress(
        self, message: ResolvableLocalizable, /
    ) -> AsyncIterator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: ResolvableLocalizable, /, *, default: bool = False
    ) -> bool:
        confirmation = next(self._confirmations)
        if confirmation is None:
            return default
        return confirmation

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: None = None,
        default: str | NothingType = Nothing,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: Pipe[str, T],
        default: str | NothingType = Nothing,
    ) -> T:
        pass

    @override
    async def ask_input(self, question, /, *, assertion=None, default=Nothing):
        value = next(self._inputs)
        if value is None:
            if default is Nothing:
                raise UserTimeoutError(
                    "Neither a predefined response nor a call default were provided."
                )
            return default
        if assertion is None:
            return value
        return assertion(value)
