"""
Provide serialization error handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from textwrap import indent
from typing import Iterator, Self

from typing_extensions import override

from betty.error import UserFacingError
from betty.locale import Localizable, Localizer, Str


class SerdeError(UserFacingError, ValueError):
    """
    A (de)serialization error.
    """

    def __init__(self, message: Localizable):
        super().__init__(message)
        self._contexts: tuple[Localizable, ...] = ()

    @override
    def localize(self, localizer: Localizer) -> str:
        localized_contexts = (context.localize(localizer) for context in self._contexts)
        return (
            super().localize(localizer)
            + "\n"
            + indent("\n".join(localized_contexts), "- ")
        ).strip()

    def raised(self, error_type: type[SerdeError]) -> bool:
        """
        Check if the error matches the given error type.
        """
        return isinstance(self, error_type)

    @property
    def contexts(self) -> tuple[Localizable, ...]:
        """
        Get the human-readable contexts describing where the error occurred in the source data.
        """
        return self._contexts

    def with_context(self, *contexts: Localizable) -> Self:
        """
        Add a message describing the error's context.
        """
        self_copy = self._copy()
        self_copy._contexts = (*self._contexts, *contexts)
        return self_copy

    def _copy(self) -> Self:
        return type(self)(self._localizable_message)


class SerdeErrorCollection(SerdeError):
    """
    A collection of zero or more (de)serialization errors.
    """

    def __init__(
        self,
        errors: list[SerdeError] | None = None,
    ):
        super().__init__(Str._("The following errors occurred"))
        self._errors: list[SerdeError] = errors or []

    def __iter__(self) -> Iterator[SerdeError]:
        yield from self._errors

    @override
    def localize(self, localizer: Localizer) -> str:
        return "\n\n".join((error.localize(localizer) for error in self._errors))

    @override
    def __reduce__(self) -> tuple[type[Self], tuple[list[SerdeError]]]:  # type: ignore[override]
        return type(self), (self._errors,)

    def __len__(self) -> int:
        return len(self._errors)

    @override
    def raised(self, error_type: type[SerdeError]) -> bool:
        return any(error.raised(error_type) for error in self._errors)

    @property
    def valid(self) -> bool:
        """
        Check that this collection contains no errors.
        """
        return len(self._errors) == 0

    @property
    def invalid(self) -> bool:
        """
        Check that this collection contains at least one error.
        """
        return not self.valid

    @contextmanager
    def assert_valid(self) -> Iterator[Self]:
        """
        Assert that this collection contains no errors.
        """
        if self.invalid:
            raise self
        with self.catch():
            yield self
        if self.invalid:  # type: ignore[redundant-expr]
            raise self

    def append(self, *errors: SerdeError) -> None:
        """
        Append errors to this collection.
        """
        for error in errors:
            if isinstance(error, SerdeErrorCollection):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    @override
    def with_context(self, *contexts: Localizable) -> Self:
        self_copy = super().with_context(*contexts)
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    @override
    def _copy(self) -> Self:
        return type(self)()

    @contextmanager
    def catch(self, *contexts: Localizable) -> Iterator[SerdeErrorCollection]:
        """
        Catch any errors raised within this context manager and add them to the collection.

        :return: A new collection that will only contain any newly raised errors.
        """
        context_errors: SerdeErrorCollection = SerdeErrorCollection()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except SerdeError as e:
            context_errors.append(e)
        self.append(*context_errors)
