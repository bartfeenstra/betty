"""
Test utilities for :py:mod:`betty.user`.
"""

import sys
from collections.abc import AsyncIterator, Iterable, MutableSequence
from contextlib import asynccontextmanager
from typing import overload

from typing_extensions import override

from betty.assertion import Assertion
from betty.locale.localizable import Localizable
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.progress import Progress
from betty.test_utils.console import _T
from betty.test_utils.progress import NoOpProgress
from betty.typing import Void, internal
from betty.user import User, UserTimeoutError


@internal
class StaticUser(User):  # pragma: no cover
    """
    A static user with predefined responses.
    """

    def __init__(
        self,
        *,
        confirmations: Iterable[bool | None] | None = None,
        inputs: Iterable[str | None] | None = None,
    ):
        self._confirmations = iter([] if confirmations is None else confirmations)
        self._inputs = iter([] if inputs is None else inputs)
        self.connected = False
        self._messages_exception: MutableSequence[BaseException] = []
        self._messages_error: MutableSequence[Localizable] = []
        self._messages_warning: MutableSequence[Localizable] = []
        self._messages_information: MutableSequence[Localizable] = []
        self._messages_debug: MutableSequence[Localizable] = []

    @override
    async def connect(self) -> None:
        self.connected = True

    @override
    async def disconnect(self) -> None:
        self.connected = False

    def _assert_message(self, fragment: str, message_type: str) -> None:
        for message in getattr(self, f"_messages_{message_type}"):  # type: ignore[attr-defined]
            if fragment in message.localize(DEFAULT_LOCALIZER):
                return
        raise AssertionError(
            f'Failed asserting that a(n) "{message_type}" message was sent containing the fragment "{fragment}".'
        )

    def assert_message_exception(self, fragment: str) -> None:
        """
        Assert that an exception message was sent.
        """
        for exception in self._messages_exception:
            if fragment in str(exception):
                return
        raise AssertionError(
            f'Failed asserting that a(n) "exception" message was sent containing the fragment "{fragment}".'
        )

    def assert_message_error(self, fragment: str) -> None:
        """
        Assert that an error message was sent.
        """
        self._assert_message(fragment, "error")

    def assert_message_warning(self, fragment: str) -> None:
        """
        Assert that a warning message was sent.
        """
        self._assert_message(fragment, "warning")

    def assert_message_information(self, fragment: str) -> None:
        """
        Assert that an information message was sent.
        """
        self._assert_message(fragment, "information")

    def assert_message_debug(self, fragment: str) -> None:
        """
        Assert that a debug message was sent.
        """
        self._assert_message(fragment, "debug")

    def _assert_not_message(self, fragment: str, message_type: str) -> None:
        for message in getattr(self, f"_messages_{message_type}"):  # type: ignore[attr-defined]
            if fragment in message.localize(DEFAULT_LOCALIZER):
                raise AssertionError(
                    f'Failed asserting that no "{message_type}" message was sent containing the fragment "{fragment}".'
                )

    def assert_not_message_exception(self, fragment: str) -> None:
        """
        Assert that no exception message was sent.
        """
        for exception in self._messages_exception:
            if fragment in str(exception):
                raise AssertionError(
                    f'Failed asserting that no "exception" message was sent containing the fragment "{fragment}".'
                )

    def assert_not_message_error(self, fragment: str) -> None:
        """
        Assert that no error message was sent.
        """
        self._assert_not_message(fragment, "error")

    def assert_not_message_warning(self, fragment: str) -> None:
        """
        Assert that no warning message was sent.
        """
        self._assert_not_message(fragment, "warning")

    def assert_not_message_information(self, fragment: str) -> None:
        """
        Assert that no information message was sent.
        """
        self._assert_not_message(fragment, "information")

    def assert_not_message_debug(self, fragment: str) -> None:
        """
        Assert that no debug message was sent.
        """
        self._assert_not_message(fragment, "debug")

    @override
    async def message_exception(self) -> None:
        exception = sys.exception()
        assert exception
        self._messages_exception.append(exception)

    @override
    async def message_error(self, message: Localizable) -> None:
        self._messages_error.append(message)

    @override
    async def message_warning(self, message: Localizable) -> None:
        self._messages_warning.append(message)

    @override
    async def message_information(self, message: Localizable) -> None:
        self._messages_information.append(message)

    @override
    async def message_debug(self, message: Localizable) -> None:
        self._messages_debug.append(message)

    @override
    @asynccontextmanager
    async def message_progress(self, message: Localizable) -> AsyncIterator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: Localizable, *, default: bool = False
    ) -> bool:
        confirmation = next(self._confirmations)
        if confirmation is None:
            return default
        return confirmation

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        default: str | type[Void] = Void,
    ) -> str:
        pass

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T],
        default: str | type[Void] = Void,
    ) -> _T:
        pass

    @override
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | _T | type[Void] = Void,
    ) -> str | _T:
        value = next(self._inputs)
        if value is None:
            if default is Void:
                raise UserTimeoutError(
                    "Neither a predefined response nor a call default were provided."
                )
            return default  # type: ignore[return-value]
        if assertion is None:
            return value
        return assertion(value)
