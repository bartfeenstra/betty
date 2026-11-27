"""
The negotiation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final, override

from typing_extensions import sentinel

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping


NoMatch = sentinel("NoMatch")


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
    def _new_unsupported(self, key: ResolvableKeyT | KeyT, /) -> UnsupportedT:
        """
        Create a new error for an unsupported key.
        """

    @abstractmethod
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | NoMatch:
        """
        Request a match by a key.
        """

    @final
    def require(self, other: ResolvableKeyT | KeyT, /) -> MatchT:
        """
        Require a match by a key.
        """
        match = self.request(other)
        if match is NoMatch:
            raise self._new_unsupported(other)
        return match


class MappingNegotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT: Exception, ValueT](
    Negotiator[KeyT, ResolvableKeyT, MatchT, UnsupportedT]
):
    """
    A negotiator backed by a mapping.
    """

    __slots__ = ("__matcher", "_resolver", "_targets")

    @final
    def __init__(
        self,
        keyer: Callable[[ValueT], Iterable[KeyT]],
        matcher: Callable[[ValueT], MatchT],
        resolver: Callable[[ResolvableKeyT | KeyT], KeyT],
        /,
        *values: ValueT,
    ):
        self.__matcher = matcher
        self._resolver: Final[Callable[[ResolvableKeyT | KeyT], KeyT]] = resolver
        self._targets: Final[Mapping[KeyT, ValueT]] = {
            key: target for target in reversed(values) for key in keyer(target)
        }

    @final
    @override
    def request(self, other: ResolvableKeyT | KeyT, /) -> MatchT | NoMatch:
        if other is None:
            return NoMatch
        other = self._resolver(other)
        target = self._targets.get(other, None)
        if target:
            return self.__matcher(target)
        return NoMatch
