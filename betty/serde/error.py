from __future__ import annotations

import copy
from contextlib import contextmanager
from textwrap import indent
from typing import Iterator, cast, Any, Self

from betty.error import UserFacingError


class SerdeError(UserFacingError, ValueError):
    """
    A serialization or deserialization error.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._contexts: tuple[str, ...] = ()

    def __str__(self) -> str:
        return (super().__str__() + '\n' + indent('\n'.join(self._contexts), '- ')).strip()

    def raised(self, error_type: type[SerdeError]) -> bool:
        return isinstance(self, error_type)

    @property
    def contexts(self) -> tuple[str, ...]:
        return self._contexts

    def with_context(self, *contexts: str) -> SerdeError:
        """
        Add a message describing the error's context.
        """
        self_copy = copy.copy(self)
        self_copy._contexts = (*self._contexts, *contexts)
        return self_copy


class SerdeErrorCollection(SerdeError):
    """
    A collection of zero or more serialization or deserialization errors.
    """

    def __init__(self):
        super().__init__()
        self._errors: list[SerdeError] = []

    def __iter__(self) -> Iterator[SerdeError]:
        yield from self._errors

    def __str__(self) -> str:
        return '\n\n'.join(map(str, self._errors))

    def __len__(self) -> int:
        return len(self._errors)

    def raised(self, error_type: type[SerdeError]) -> bool:
        for error in self._errors:
            if error.raised(error_type):
                return True
        return False

    @property
    def valid(self) -> bool:
        return len(self._errors) == 0

    @property
    def invalid(self) -> bool:
        return not self.valid

    @contextmanager
    def assert_valid(self) -> Iterator[Self]:
        if self.invalid:
            raise self
        with self.catch():
            yield self
        if self.invalid:
            raise self

    def append(self, *errors: SerdeError) -> None:
        for error in errors:
            if isinstance(error, SerdeErrorCollection):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    def with_context(self, *contexts: str) -> SerdeErrorCollection:
        self_copy = cast(SerdeErrorCollection, super().with_context(*contexts))
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    @contextmanager
    def catch(self, *contexts: str) -> Iterator[SerdeErrorCollection]:
        context_errors: SerdeErrorCollection = SerdeErrorCollection()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except SerdeError as e:
            context_errors.append(e)
        self.append(*context_errors)
