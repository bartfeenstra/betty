"""
Test utilities for :py:mod:`betty.user`.
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, overload, override

from betty.localizer import default_localizer
from betty.progresses.no_op import NoOpProgress
from betty.typing import Void, VoidType
from betty.user import User, UserTimeoutError, Verbosity

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Collection, Iterable, MutableSequence

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.progress import Progress


class StaticUser(User):
    """
    A static user with predefined responses.
    """

    verbosity = Verbosity.DEFAULT

    def __init__(
        self,
        *,
        confirmations: Iterable[bool | None] = (),
        inputs: Iterable[str | None] = (),
    ):
        self._confirmations = iter(confirmations)
        self._inputs = iter(inputs)
        self._messages_exception: MutableSequence[BaseException] = []
        self._messages_error: MutableSequence[ResolvableLocalizable] = []
        self._messages_warning: MutableSequence[ResolvableLocalizable] = []
        self._messages_information: MutableSequence[ResolvableLocalizable] = []
        self._messages_information_details: MutableSequence[ResolvableLocalizable] = []
        self._messages_debug: MutableSequence[ResolvableLocalizable] = []
        self._messages_log: MutableSequence[logging.LogRecord] = []
        self._log_formatter = logging.Formatter()

    @override
    async def set_verbosity(self, verbosity: Verbosity, /) -> None:
        self.verbosity = verbosity

    def _format_fragments(self, fragments: str | Iterable[str]) -> str:
        if isinstance(fragments, str):
            fragments = [fragments]
        return ", ".join(f'"{fragment}"' for fragment in fragments)

    def _message_contains(self, message: str, fragments: Iterable[str]) -> bool:
        return all(fragment in message for fragment in fragments)

    def _assert_message(
        self,
        fragments: str | Iterable[str],
        message_type: str,
        messages: Collection[str],
    ) -> None:
        if isinstance(fragments, str):
            fragments = [fragments]
        for message in messages:
            if self._message_contains(message, fragments):
                return
        raise AssertionError(
            f'Failed asserting that a(n) "{message_type}" message was sent containing the fragment(s) {self._format_fragments(fragments)}.'
        )

    def _assert_localizable_message(
        self, fragments: str | Iterable[str], message_type: str
    ) -> None:
        self._assert_message(
            fragments,
            message_type,
            [
                default_localizer.localize(message)
                for message in getattr(self, f"_messages_{message_type}")
            ],
        )

    def assert_message_exception(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that an exception message was sent.
        """
        self._assert_message(
            fragments, "exception", list(map(str, self._messages_exception))
        )

    def assert_message_error(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that an error message was sent.
        """
        self._assert_localizable_message(fragments, "error")

    def assert_message_warning(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that a warning message was sent.
        """
        self._assert_localizable_message(fragments, "warning")

    def assert_message_information(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that an information message was sent.
        """
        self._assert_localizable_message(fragments, "information")

    def assert_message_information_details(
        self, fragments: str | Iterable[str]
    ) -> None:
        """
        Assert that a detailed information message was sent.
        """
        self._assert_localizable_message(fragments, "information_details")

    def assert_message_debug(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that a debug message was sent.
        """
        self._assert_localizable_message(fragments, "debug")

    def assert_message_log(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that a log message was sent.
        """
        self._assert_message(
            fragments, "log", list(map(self._log_formatter.format, self._messages_log))
        )

    def _assert_not_message(
        self,
        fragments: str | Iterable[str],
        message_type: str,
        messages: Collection[str],
    ) -> None:
        if isinstance(fragments, str):
            fragments = [fragments]
        for message in messages:
            if self._message_contains(message, fragments):
                raise AssertionError(
                    f'Failed asserting that a(n) "{message_type}" message was sent containing the fragment(s) {self._format_fragments(fragments)}.'
                )

    def _assert_not_localizable_message(
        self, fragments: str | Iterable[str], message_type: str
    ) -> None:
        self._assert_not_message(
            fragments,
            message_type,
            [
                default_localizer.localize(message)
                for message in getattr(self, f"_messages_{message_type}")
            ],
        )

    def assert_not_message_exception(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no exception message was sent.
        """
        self._assert_not_message(
            fragments, "exception", list(map(str, self._messages_exception))
        )

    def assert_not_message_error(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no error message was sent.
        """
        self._assert_not_localizable_message(fragments, "error")

    def assert_not_message_warning(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no warning message was sent.
        """
        self._assert_not_localizable_message(fragments, "warning")

    def assert_not_message_information(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no information message was sent.
        """
        self._assert_not_localizable_message(fragments, "information")

    def assert_not_message_information_details(
        self, fragments: str | Iterable[str]
    ) -> None:
        """
        Assert that no detailed information message was sent.
        """
        self._assert_not_localizable_message(fragments, "information_details")

    def assert_not_message_debug(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no debug message was sent.
        """
        self._assert_not_localizable_message(fragments, "debug")

    def assert_not_message_log(self, fragments: str | Iterable[str]) -> None:
        """
        Assert that no log message was sent.
        """
        self._assert_not_message(
            fragments, "log", list(map(self._log_formatter.format, self._messages_log))
        )

    @override
    async def message_exception(self) -> None:
        exception = sys.exception()
        assert exception
        self._messages_exception.append(exception)

    @override
    async def message_error(self, message: ResolvableLocalizable, /) -> None:
        self._messages_error.append(message)

    @override
    async def message_warning(self, message: ResolvableLocalizable, /) -> None:
        self._messages_warning.append(message)

    @override
    async def message_information(self, message: ResolvableLocalizable, /) -> None:
        self._messages_information.append(message)

    @override
    async def message_information_details(
        self, message: ResolvableLocalizable, /
    ) -> None:
        self._messages_information_details.append(message)

    @override
    async def message_debug(self, message: ResolvableLocalizable, /) -> None:
        self._messages_debug.append(message)

    @override
    async def message_log(self, message: logging.LogRecord, /) -> None:
        self._messages_log.append(message)

    @override
    @asynccontextmanager
    async def message_progress(
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
        default: str | VoidType = Void,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: Pipe[str, T],
        default: str | VoidType = Void,
    ) -> T:
        pass

    @override
    async def ask_input(self, question, /, *, assertion=None, default=Void):
        value = next(self._inputs)
        if value is None:
            if default is Void:
                raise UserTimeoutError(
                    "Neither a predefined response nor a call default were provided."
                )
            return default
        if assertion is None:
            return value
        return assertion(value)
