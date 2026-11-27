"""
The negotiation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final, override

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


class Negotiator[
    KeyT,
    ResolvableKeyT,
    MatchT,
    UnsupportedT: Exception,
](metaclass=ABCMeta):
    """
    Negotiate the best match against available targets.
    """

    __slots__ = ()

    @abstractmethod
    def new_unsupported(self, key: KeyT, /) -> UnsupportedT:
        """
        Create a new error for an unsupported key.
        """

    @abstractmethod
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | None:
        """
        Request a match by a key.
        """

    @final
    def require(self, other: ResolvableKeyT | KeyT, /) -> MatchT:
        """
        Require a match by a key.
        """
        if match := self.request(other):
            return match
        raise self.new_unsupported(other)


class MappingNegotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT: Exception, ValueT](
    Negotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT]
):
    """
    A negotiator backed by a mapping.
    """

    __slots__ = ("_matcher", "_resolver", "_targets")

    @final
    def __init__(
        self,
        keyer: Callable[[ValueT], Iterable[KeyT]],
        matcher: Callable[[ValueT], MatchT],
        resolver: Callable[[ResolvableKeyT | KeyT], KeyT],
        /,
        *values: ValueT,
    ):
        self._matcher = matcher
        self._resolver = resolver
        self._targets = {
            key: target for target in reversed(values) for key in keyer(target)
        }

    @final
    @override
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | None:
        if other is None:
            return None
        other = self._resolver(other)
        target = self._targets.get(other, None)
        if target:
            return self._matcher(target)
        return None
