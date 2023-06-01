from __future__ import annotations

import copy
from contextlib import contextmanager
from textwrap import indent
from typing import Iterator, Tuple, cast, Type

from betty.classtools import Repr
from betty.error import UserFacingError

try:
    from typing_extensions import Self
except ModuleNotFoundError:  # pragma: no cover
    from typing import Self  # type: ignore  # pragma: no cover


class ConfigurationError(UserFacingError, ValueError):
    """
    A configuration error.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: Tuple[str, ...] = ()

    def __str__(self):
        return (super().__str__() + '\n' + indent('\n'.join(self._contexts), '- ')).strip()

    def raised(self, error_type: Type[ConfigurationError]) -> bool:
        return isinstance(self, error_type)

    @property
    def contexts(self) -> Tuple[str, ...]:
        return self._contexts

    def with_context(self, *contexts: str) -> ConfigurationError:
        """
        Add a message describing the error's context.
        """
        self_copy = copy.copy(self)
        self_copy._contexts = (*self._contexts, *contexts)
        return self_copy


class ConfigurationErrorCollection(ConfigurationError, Repr):
    """
    A collection of zero or more configuration errors.
    """

    def __init__(self):
        super().__init__()
        self._errors = []

    def __iter__(self) -> Iterator[ConfigurationError]:
        yield from self._errors

    def __str__(self) -> str:
        return '\n\n'.join(map(str, self._errors))

    def __len__(self) -> int:
        return len(self._errors)

    def raised(self, error_type: Type[ConfigurationError]) -> bool:
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

    def append(self, *errors: ConfigurationError) -> None:
        for error in errors:
            if isinstance(error, ConfigurationErrorCollection):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    def with_context(self, *contexts: str) -> ConfigurationErrorCollection:
        self_copy = cast(ConfigurationErrorCollection, super().with_context(*contexts))
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    @contextmanager
    def catch(self, *contexts: str) -> Iterator[ConfigurationErrorCollection]:
        context_errors: ConfigurationErrorCollection = ConfigurationErrorCollection()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except ConfigurationError as e:
            context_errors.append(e)
        self.append(*context_errors)
