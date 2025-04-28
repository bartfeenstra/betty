"""
Provide assertion failures.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from textwrap import indent
from typing import TYPE_CHECKING, Self, TypeAlias, TypeVar

from typing_extensions import override

from betty.error import UserFacingError
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import Localizable, _
from betty.locale.localized import LocalizedStr

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence, Sequence

    from betty.locale.localizer import Localizer


_AssertionContextValueT = TypeVar("_AssertionContextValueT")


class AssertionContext(ABC):
    """
    The context in which an assertion is invoked.
    """

    @abstractmethod
    def format(self) -> str:
        """
        Format this context to a string.
        """


class Attr(AssertionContext):
    """
    An object attribute context.
    """

    def __init__(self, attr: str):
        self._attr = attr

    @override
    def format(self) -> str:
        return f".{self._attr}"


class Index(AssertionContext):
    """
    A sequence index context.
    """

    def __init__(self, index: int):
        self._index = index

    @override
    def format(self) -> str:
        return f"[{self._index}]"


class Key(AssertionContext):
    """
    A mapping key context.
    """

    def __init__(self, key: str):
        self._key = key

    @override
    def format(self) -> str:
        return f'["{self._key}"]'


Contextey: TypeAlias = AssertionContext | Localizable


class _Contexts(Localizable):
    def __init__(self, context: AssertionContext):
        self.contexts: MutableSequence[AssertionContext] = [context]

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return LocalizedStr(
            "data" + "".join(context.format() for context in self.contexts),
            locale=UNDETERMINED_LOCALE,
        )


def localizable_contexts(*contexts: Contextey) -> Sequence[Localizable]:
    """
    The contexts as :py:class:`betty.locale.localizable.Localizable` instances.
    """
    localizable_contexts: MutableSequence[Localizable] = []
    for context in contexts:
        if isinstance(context, Localizable):
            localizable_contexts.append(context)
        else:
            try:
                last_context = localizable_contexts[-1]
            except IndexError:
                pass
            else:
                if isinstance(last_context, _Contexts):
                    last_context.contexts.append(context)
                    continue
            localizable_contexts.append(_Contexts(context))
    return localizable_contexts


class AssertionFailed(UserFacingError, ValueError):
    """
    An assertion failure.
    """

    def __init__(
        self, message: Localizable, *, contexts: tuple[Contextey, ...] | None = None
    ):
        super().__init__(message)
        self._contexts: tuple[Contextey, ...] = contexts or ()

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return LocalizedStr(
            (
                super().localize(localizer)
                + "\n"
                + indent(
                    "\n".join(
                        context.localize(localizer)
                        for context in localizable_contexts(*self.contexts)
                    ),
                    "- ",
                )
            ).strip(),
            locale=localizer.locale,
        )

    def raised(self, error_type: type[AssertionFailed]) -> bool:
        """
        Check if the error matches the given error type.
        """
        return isinstance(self, error_type)

    @property
    def contexts(self) -> tuple[Contextey, ...]:
        """
        Get the human-readable contexts describing where the error occurred in the source data.
        """
        return self._contexts

    def with_context(self, *contexts: Contextey) -> Self:
        """
        Add a message describing the error's context.
        """
        self_copy = self._copy()
        self_copy._contexts = (*reversed(contexts), *self._contexts)
        return self_copy

    def _copy(self) -> Self:
        return type(self)(self._localizable_message)


class AssertionFailedGroup(AssertionFailed):
    """
    A group of zero or more assertion failures.
    """

    def __init__(
        self,
        errors: Sequence[AssertionFailed] | None = None,
    ):
        super().__init__(_("The following errors occurred"))
        self._errors: MutableSequence[AssertionFailed] = []
        if errors is not None:
            self.append(*errors)

    def __iter__(self) -> Iterator[AssertionFailed]:
        yield from self._errors

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return LocalizedStr(
            "\n\n".join(error.localize(localizer) for error in self._errors),
            locale=localizer.locale,
        )

    def __len__(self) -> int:
        return len(self._errors)

    @override
    def raised(self, error_type: type[AssertionFailed]) -> bool:
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
    def assert_valid(self, *contexts: Contextey) -> Iterator[Self]:
        """
        Assert that this collection contains no errors.
        """
        if self.invalid:
            raise self
        with self.catch(*contexts):
            yield self
        if self.invalid:  # type: ignore[redundant-expr]
            raise self

    def append(self, *errors: AssertionFailed) -> None:
        """
        Append errors to this collection.
        """
        for error in errors:
            if isinstance(error, AssertionFailedGroup):
                self.append(*error)
            else:
                self._errors.append(error.with_context(*self._contexts))

    @override
    def with_context(self, *contexts: Contextey) -> Self:
        self_copy = super().with_context(*contexts)
        self_copy._errors = [error.with_context(*contexts) for error in self._errors]
        return self_copy

    @override
    def _copy(self) -> Self:
        return type(self)()

    @contextmanager
    def catch(self, *contexts: Contextey) -> Iterator[AssertionFailedGroup]:
        """
        Catch any errors raised within this context manager and add them to the collection.

        :return: A new collection that will only contain any newly raised errors.
        """
        context_errors: AssertionFailedGroup = AssertionFailedGroup()
        if contexts:
            context_errors = context_errors.with_context(*contexts)
        try:
            yield context_errors
        except AssertionFailed as e:
            context_errors.append(e)
        self.append(*context_errors)
