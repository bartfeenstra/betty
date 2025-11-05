"""
Provide exception handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.data import Selectors
from betty.locale.localizable import Lines, Localizable, UnorderedList

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence
    from types import TracebackType

    from betty.data import Context
    from betty.locale.localized import Localized
    from betty.locale.localizer import Localizer


class HumanFacingException(Exception, Localizable):
    """
    A localizable, human-facing exception.

    When encountering an exception that extends this base class, Betty will show the localized exception message, and
    no stack trace.
    """

    def __init__(
        self, message: Localizable, *, contexts: Sequence[Context] | None = None
    ):
        from betty.locale.localizer import DEFAULT_LOCALIZER

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message
        self._contexts = [] if contexts is None else list(contexts)

    @override
    def __str__(self) -> str:
        from betty.locale.localizer import DEFAULT_LOCALIZER

        return self.localize(DEFAULT_LOCALIZER)

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return Lines(
            self._localizable_message, UnorderedList(*Selectors.reduce(*self.contexts))
        ).localize(localizer)

    @property
    def contexts(self) -> Sequence[Context]:
        """
        Get the human-readable contexts describing where the error occurred in the source data.
        """
        return self._contexts

    def within_context(self, *contexts: Context) -> None:
        """
        Adds the given context(s) to the exception.
        """
        self._contexts.extend(contexts)


@final
class Collector:
    """
    Collect exceptions and raise them as an exception group.
    """

    def __init__(self):
        self._exceptions: MutableSequence[Exception] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._exceptions:
            raise ExceptionGroup("Some errors occurred", self._exceptions)

    @contextmanager
    def collect(self, exception_type: type[Exception] = Exception) -> Iterator[None]:
        """
        Collect and suppress exceptions of the given type.
        """
        try:
            yield None
        except exception_type as exception:
            self._exceptions.append(exception)


@contextmanager
def within_context(*contexts: Context) -> Iterator[None]:
    """
    Adds the given context(s) to caught :py:class:`betty.exception.HumanFacingException`.
    """
    try:
        yield None
    except HumanFacingException as exception:
        exception.within_context(*contexts)
        raise
